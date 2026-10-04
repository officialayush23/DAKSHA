"""
Commerce policies, evaluated by the engine's policy_gate BEFORE a tool runs.

Each policy returns allow / deny / approve(customer|staff), optionally with
normalized arguments. The numbers come from app/ai/policy/company_policy.py,
which used to be injected only into prompts; here they are code.

Services still do their own validation (ownership, stock, windows). The gate
is the earlier, cheaper line: it decides whether a human must look first.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.agentic.core.registry import PolicyDecision, ToolContext

REFUND_APPROVAL_THRESHOLD = 5000.0     # ₹: returns worth more than this need staff sign-off
MARKETING_COOLDOWN_DAYS = 7


def _db():
    from app.core.database import SessionLocal
    return SessionLocal()


def no_proactive(tc: ToolContext, a) -> PolicyDecision:
    if tc.channel == "proactive":
        return PolicyDecision("deny", "no_autonomous_purchase", "proactive runs may not start or pay for orders")
    return PolicyDecision("allow", "customer_initiated")


def place_order_policy(tc: ToolContext, a) -> PolicyDecision:
    if tc.channel == "proactive":
        return PolicyDecision("deny", "no_autonomous_purchase", "proactive runs may not pay for orders")
    co = (tc.ctx or {}).get("checkout")
    if not co:
        return PolicyDecision("deny", "checkout_required", "no open checkout; start checkout first")
    amount = co["locked_price"] - co.get("discount", 0)
    pts = getattr(a, "redeem_points", 0) or 0
    if pts:
        from app.ai.policy.company_policy import validate_loyalty_redemption
        ok, why = validate_loyalty_redemption(pts, amount)
        if not ok:
            return PolicyDecision("deny", "loyalty_redemption", why)
        if pts > ((tc.ctx or {}).get("loyalty_points") or 0):
            return PolicyDecision("deny", "loyalty_balance", "not enough loyalty points")
    if co["fulfillment"] == "delivery" and not getattr(a, "address_id", None):
        return PolicyDecision("deny", "address_required", "delivery orders need an address_id from list_addresses")
    if getattr(a, "address_id", None):
        mine = {x["address_id"] for x in (tc.ctx or {}).get("addresses", [])}
        if str(a.address_id) not in mine:
            return PolicyDecision("deny", "address_ownership", "that address is not on this account")
    return PolicyDecision("approve", "payment_confirmation",
                          f"Place {co['fulfillment']} order for ₹{amount:.0f}" + (f" using {pts} points" if pts else "") + "?",
                          approver="customer")


def offer_policy(tc: ToolContext, a) -> PolicyDecision:
    from app.ai.policy.company_policy import OFFER_POLICY, cap_offer_discount
    tier = ((tc.ctx or {}).get("customer") or {}).get("tier", "bronze")
    live = len((tc.ctx or {}).get("offers", []))
    if live >= OFFER_POLICY.max_active_offers_per_user:
        return PolicyDecision("deny", "max_active_offers", f"customer already has {live} live offers")
    args = None
    if getattr(a, "percent", None):
        capped = cap_offer_discount(a.percent, tier)
        if capped < a.percent:
            args = {"percent": capped}
    if tc.channel == "proactive":
        return PolicyDecision("approve", "proactive_offer", f"Create a personal offer for a {tier} customer", approver="staff", args=args)
    return PolicyDecision("allow", "tier_cap", f"capped to {tier} limit" if args else "", args=args)


def return_policy(tc: ToolContext, a) -> PolicyDecision:
    try:
        with _db() as db:
            ref = (a.order_ref or "").strip().lstrip("#").lower()
            row = db.execute(text("""
                SELECT o.order_status, oi.price_at_purchase, oi.quantity
                FROM orders o JOIN order_items oi ON oi.order_id = o.id
                WHERE o.user_id = :u AND o.id::text LIKE :p AND oi.product_variant_id = :v LIMIT 1
            """), {"u": tc.user_id, "p": f"{ref}%", "v": str(a.variant_id)}).first()
    except Exception:
        row = None
    if not row:
        return PolicyDecision("deny", "return_item_ownership", "that item is not in one of this customer's orders")
    if row.order_status != "delivered":
        return PolicyDecision("deny", "return_requires_delivery", "only delivered orders can be returned")
    value = float(row.price_at_purchase or 0) * min(a.quantity, row.quantity)
    if value > REFUND_APPROVAL_THRESHOLD:
        return PolicyDecision("approve", "high_value_refund", f"Refund of ₹{value:.0f} exceeds ₹{REFUND_APPROVAL_THRESHOLD:.0f}",
                              approver="staff")
    return PolicyDecision("allow", "return_window_and_value")


def cancel_policy(tc: ToolContext, a) -> PolicyDecision:
    from app.ai.policy.company_policy import validate_cancellation
    try:
        with _db() as db:
            ref = (a.order_ref or "").strip().lstrip("#").lower()
            row = db.execute(text("SELECT order_status FROM orders WHERE user_id = :u AND id::text LIKE :p LIMIT 1"),
                             {"u": tc.user_id, "p": f"{ref}%"}).first()
    except Exception:
        row = None
    if not row:
        return PolicyDecision("deny", "order_ownership", "no such order on this account")
    ok, fee, msg = validate_cancellation(row.order_status)
    if not ok:
        return PolicyDecision("deny", "cancellation_window", msg)
    if fee > 0:
        return PolicyDecision("approve", "cancellation_fee", f"{msg} Cancel anyway?", approver="customer")
    return PolicyDecision("allow", "free_cancellation")


def complaint_policy(tc: ToolContext, a) -> PolicyDecision:
    return PolicyDecision("allow", "complaint_intake")


def message_policy(tc: ToolContext, a) -> PolicyDecision:
    transactional = {"post_delivery_feedback", "order_update", "pickup_reminder"}
    if a.purpose in transactional:
        return PolicyDecision("allow", "transactional_message")
    try:
        with _db() as db:
            since = datetime.now(timezone.utc) - timedelta(days=MARKETING_COOLDOWN_DAYS)
            n = db.execute(text("""SELECT count(*) FROM outbound_messages WHERE user_id = :u AND sent_at > :s
                                   AND message_type IN ('abandoned_cart','wishlist_offer','reengagement','wishlist_offer')"""),
                           {"u": tc.user_id, "s": since}).scalar()
    except Exception:
        n = 0
    if n:
        return PolicyDecision("deny", "marketing_cooldown", f"a marketing message was sent in the last {MARKETING_COOLDOWN_DAYS} days")
    return PolicyDecision("approve", "marketing_message", f"Send '{a.subject}' ({a.purpose}) via {', '.join(a.channels)}",
                          approver="staff")

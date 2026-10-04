"""
Unified customer context.

Every turn, on every channel (web/PWA, kiosk, Telegram, proactive jobs), the
engine rebuilds the same picture of the customer from the system of record:
profile and tier, loyalty points, the single shared cart, any open checkout,
recent orders, open returns/complaints, live offers, saved addresses, the
kiosk store if there is one, the taste profile, which channels they have used
recently, and whether a human is already handling the conversation.

Because it is rebuilt from the database (not carried in chat history), a
customer who adds a jacket on their phone and walks up to a kiosk sees the
same cart and the same agent knowledge.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from sqlalchemy import text

from app.agentic.core.registry import ToolContext


def _u(v):
    try:
        return uuid.UUID(str(v)) if v else None
    except (ValueError, TypeError):
        return None


def ensure_web_session(db, user_id, channel: str):
    """Return the user's live sessions.id row (checkout/events FK target)."""
    from app.enums.db_enums import ChannelEnum
    from app.models.models import UserSession
    ch = {"pwa": "app"}.get(channel, channel)
    try:
        ch_enum = ChannelEnum(ch)
    except ValueError:
        ch_enum = ChannelEnum.web
    s = (db.query(UserSession).filter(UserSession.user_id == user_id, UserSession.ended_at.is_(None))
         .order_by(UserSession.started_at.desc()).first())
    if not s:
        s = UserSession(user_id=user_id, primary_channel=ch_enum, active_channel=ch_enum)
        db.add(s)
        db.commit()
        db.refresh(s)
    elif s.active_channel != ch_enum and channel != "proactive":
        s.active_channel = ch_enum
        db.commit()
    return s


def load_context(tc: ToolContext) -> Dict[str, Any]:
    from app.core.database import SessionLocal
    from app.models.models import CheckoutSession, User
    from app.services.cart_service import get_hydrated_cart
    from app.services.loyalty_service import get_balance

    uid = _u(tc.user_id)
    if not uid:
        return {"customer": None, "channel": tc.channel}
    ctx: Dict[str, Any] = {"channel": tc.channel}
    with SessionLocal() as db:
        user = db.get(User, uid)
        if not user:
            return {"customer": None, "channel": tc.channel}
        web = ensure_web_session(db, uid, tc.channel)
        ctx["web_session_id"] = str(web.id)
        ctx["customer"] = {"name": user.name, "tier": (user.loyalty_tier or "bronze"), "has_email": bool(user.email),
                           "has_phone": bool(user.phone), "member_since": user.created_at.date().isoformat() if user.created_at else None}
        try:
            ctx["loyalty_points"] = int(get_balance(db, uid))
        except Exception:
            ctx["loyalty_points"] = None

        cart = get_hydrated_cart(db, uid)
        ctx["cart"] = {"cart_id": cart.get("cart_id"), "items": [
            {"variant_id": i["variant_id"], "name": i["name"], "color": i["color"], "size": i["size"],
             "qty": i["quantity"], "unit_price": i["unit_price"]} for i in cart.get("items", [])],
            "total": cart.get("grand_total", 0.0)}

        co = (db.query(CheckoutSession).filter(CheckoutSession.user_id == uid)
              .order_by(CheckoutSession.updated_at.desc()).first())
        if co and getattr(co.state, "value", co.state) not in ("ORDER_CONFIRMED", "CANCELLED", "ROLLED_BACK"):
            ctx["checkout"] = {"checkout_id": str(co.id), "state": getattr(co.state, "value", co.state),
                               "fulfillment": getattr(co.fulfillment_type, "value", co.fulfillment_type),
                               "locked_price": float(co.locked_price or 0), "discount": float(co.discount_amount or 0),
                               "store_id": str(co.store_id) if co.store_id else None,
                               "hold_expires": co.reserved_until.isoformat() if co.reserved_until else None}

        rows = db.execute(text("""
            SELECT o.id, o.order_status, o.total_amount, o.created_at, o.fulfillment_type,
                   (SELECT count(*) FROM order_items oi WHERE oi.order_id = o.id) AS n
            FROM orders o WHERE o.user_id = :u ORDER BY o.created_at DESC LIMIT 5
        """), {"u": str(uid)}).fetchall()
        ctx["recent_orders"] = [{"ref": str(r.id)[:8], "order_id": str(r.id), "status": r.order_status,
                                 "total": float(r.total_amount or 0), "items": r.n,
                                 "fulfillment": r.fulfillment_type,
                                 "placed": r.created_at.date().isoformat() if r.created_at else None} for r in rows]

        counts = db.execute(text("""
            SELECT
              (SELECT count(*) FROM returns r JOIN orders o ON o.id = r.order_id
                 WHERE o.user_id = :u AND r.status IN ('requested','approved')) AS open_returns,
              (SELECT count(*) FROM exchanges e JOIN orders o ON o.id = e.order_id
                 WHERE o.user_id = :u AND e.status IN ('requested','approved')) AS open_exchanges,
              (SELECT count(*) FROM complaints c WHERE c.user_id = :u AND c.status IN ('open','in_progress')) AS open_complaints,
              (SELECT count(*) FROM user_wishlist w WHERE w.user_id = :u) AS wishlist
        """), {"u": str(uid)}).first()
        ctx["support"] = {"open_returns": counts.open_returns, "open_exchanges": counts.open_exchanges,
                          "open_complaints": counts.open_complaints}
        ctx["wishlist_items"] = counts.wishlist

        offers = db.execute(text("""
            SELECT id, offer_name, expires_at FROM user_personalized_offers
            WHERE user_id = :u AND is_redeemed = false AND expires_at > now() ORDER BY created_at DESC LIMIT 3
        """), {"u": str(uid)}).fetchall()
        ctx["offers"] = [{"offer_id": str(o.id), "name": o.offer_name} for o in offers]

        addrs = db.execute(text("""
            SELECT id, label, city, is_default FROM user_addresses WHERE user_id = :u ORDER BY is_default DESC, created_at DESC LIMIT 4
        """), {"u": str(uid)}).fetchall()
        ctx["addresses"] = [{"address_id": str(a.id), "label": a.label or "Address", "city": a.city,
                             "default": a.is_default} for a in addrs]

        if tc.store_id:
            st = db.execute(text("SELECT id, name, city FROM stores WHERE id = :s"), {"s": str(tc.store_id)}).first()
            if st:
                ctx["store"] = {"store_id": str(st.id), "name": st.name, "city": st.city}

        pref = db.execute(text("SELECT summary_text FROM user_preference_summary WHERE user_id = :u"),
                          {"u": str(uid)}).first()
        ctx["taste_profile"] = (pref.summary_text or "")[:400] if pref else None

        since = datetime.now(timezone.utc) - timedelta(days=30)
        chans = db.execute(text("""
            SELECT DISTINCT channel FROM chat_sessions WHERE user_id = :u AND updated_at > :since
        """), {"u": str(uid), "since": since}).fetchall()
        ctx["channels_used"] = sorted({c.channel for c in chans} | {tc.channel})

        if tc.session_id:
            h = db.execute(text("""
                SELECT id FROM agent_handoffs WHERE chat_session_id = :s AND status IN ('open','in_progress')
                ORDER BY created_at DESC LIMIT 1
            """), {"s": str(tc.session_id)}).first()
            ctx["open_handoff"] = str(h.id) if h else None
    return ctx


def render_context(ctx: Dict[str, Any]) -> str:
    """Compact, model-facing view. Raw UUIDs only where tools need them."""
    if not ctx or not ctx.get("customer"):
        return f"Guest on channel {ctx.get('channel', 'web')} (not signed in)."
    c = ctx["customer"]
    lines = [f"Customer: {c.get('name') or 'unknown'} · tier {c['tier']} · points {ctx.get('loyalty_points')} · "
             f"channel {ctx.get('channel')} (used recently: {', '.join(ctx.get('channels_used', []))})"]
    if ctx.get("store"):
        lines.append(f"At kiosk in store: {ctx['store']['name']} ({ctx['store']['city']}) store_id={ctx['store']['store_id']}")
    cart = ctx.get("cart") or {}
    if cart.get("items"):
        items = "; ".join(f"{i['name']} {i.get('color') or ''}/{i.get('size') or ''} x{i['qty']} @₹{i['unit_price']:.0f} (variant_id={i['variant_id']})"
                          for i in cart["items"][:8])
        lines.append(f"Cart (total ₹{cart['total']:.0f}): {items}")
    else:
        lines.append("Cart: empty")
    if ctx.get("checkout"):
        co = ctx["checkout"]
        lines.append(f"Open checkout: {co['fulfillment']} · locked ₹{co['locked_price']:.0f} · discount ₹{co['discount']:.0f} · "
                     f"state {co['state']} · hold until {co['hold_expires']}")
    if ctx.get("recent_orders"):
        lines.append("Recent orders: " + "; ".join(f"#{o['ref']} {o['status']} ₹{o['total']:.0f} ({o['items']} items, {o['placed']})"
                                                     for o in ctx["recent_orders"]))
    s = ctx.get("support") or {}
    if any(s.values()):
        lines.append(f"Open support items: returns {s['open_returns']}, exchanges {s['open_exchanges']}, complaints {s['open_complaints']}")
    if ctx.get("offers"):
        lines.append("Live personal offers: " + "; ".join(f"{o['name']} (offer_id={o['offer_id']})" for o in ctx["offers"]))
    if ctx.get("addresses"):
        lines.append("Saved addresses: " + "; ".join(f"{a['label']} in {a['city']}{' [default]' if a['default'] else ''} (address_id={a['address_id']})"
                                                       for a in ctx["addresses"]))
    if ctx.get("taste_profile"):
        lines.append(f"Taste profile: {ctx['taste_profile']}")
    return "\n".join(lines)

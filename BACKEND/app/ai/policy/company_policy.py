"""
DAKSHA Company Policy — Single Source of Truth
================================================
This module defines all business rules that govern agent behaviour.
Every agent's system prompt is built using `build_agent_prompt()` which
injects the relevant policy section automatically.

Changing a rule here instantly propagates to all agents — no agent file
edits required.
"""

import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. POLICY DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ReturnPolicy:
    window_days: int = 7                        # days after delivery
    allowed_statuses: tuple = ("delivered",)    # order must be in this status
    excluded_categories: tuple = (
        "innerwear", "swimwear", "lingerie", "personalised"
    )
    excluded_if_discount_above_pct: int = 50    # items >50% off are final sale
    requires_tags: bool = True                  # original tags must be attached
    requires_unworn: bool = True
    max_per_order: int = 1                      # one return request per order

@dataclass(frozen=True)
class ExchangePolicy:
    window_days: int = 14
    allowed_reasons: tuple = ("size", "color", "defect", "wrong_item")
    max_per_order: int = 1
    allowed_statuses: tuple = ("delivered",)

@dataclass(frozen=True)
class OfferPolicy:
    # Max discount % an agent can generate autonomously per tier
    max_discount_pct: dict = field(default_factory=lambda: {
        "bronze":   10,
        "silver":   15,
        "gold":     20,
        "platinum": 30,
        "default":  10,     # unauthenticated / unknown tier
    })
    min_cart_value_for_offer: float = 299.0     # ₹299 minimum
    max_flat_discount: float = 500.0            # absolute ₹ ceiling any agent can give
    offer_expiry_hours: int = 24                # personalized offers expire in 24h
    max_active_offers_per_user: int = 3         # agent won't generate more than 3 live offers

@dataclass(frozen=True)
class LoyaltyPolicy:
    points_per_rupee: float = 0.1               # ₹10 spent → 1 point
    rupees_per_100_points: float = 10.0         # 100 pts = ₹10 off
    min_cart_for_redemption: float = 500.0      # ₹500 min cart to redeem
    min_points_to_redeem: int = 100
    max_redemption_pct_of_cart: float = 0.20    # can't redeem more than 20% of cart value
    points_expiry_days: int = 365

@dataclass(frozen=True)
class CancellationPolicy:
    free_before_status: str = "packed"          # free cancel before packing starts
    fee_after_packed: float = 50.0              # ₹50 fee if packed
    not_allowed_after_status: str = "shipped"   # cannot cancel after shipped

@dataclass(frozen=True)
class DeliveryPolicy:
    standard_sla_days: tuple = (3, 5)          # (min, max) business days
    express_sla_days: tuple = (0, 1)
    reschedule_cutoff_hours: int = 48           # must reschedule ≥48h before window
    max_reschedule_attempts: int = 2
    delivery_attempt_max: int = 3               # after 3 failed attempts → return to warehouse

@dataclass(frozen=True)
class HandoffPolicy:
    max_agent_failures_before_handoff: int = 3
    trigger_keywords: tuple = (
        "speak to human", "talk to a person", "human agent",
        "real person", "your manager", "escalate", "not helpful",
    )
    complaint_severity_auto_escalate: str = "critical"  # severity level that forces handoff
    payment_failures_before_escalate: int = 2

@dataclass(frozen=True)
class PaymentPolicy:
    max_payment_retry_attempts: int = 3
    cod_max_order_value: float = 5000.0         # Cash on Delivery only up to ₹5000
    supported_methods: tuple = ("card", "upi", "cod", "wallet", "loyalty_points")
    loyalty_points_max_contribution_pct: float = 0.20   # loyalty can cover up to 20% of total

# ─────────────────────────────────────────────────────────────────────────────
# 2. INSTANTIATED POLICY OBJECTS (import these in agents)
# ─────────────────────────────────────────────────────────────────────────────

RETURN_POLICY      = ReturnPolicy()
EXCHANGE_POLICY    = ExchangePolicy()
OFFER_POLICY       = OfferPolicy()
LOYALTY_POLICY     = LoyaltyPolicy()
CANCEL_POLICY      = CancellationPolicy()
DELIVERY_POLICY    = DeliveryPolicy()
HANDOFF_POLICY     = HandoffPolicy()
PAYMENT_POLICY     = PaymentPolicy()

# ─────────────────────────────────────────────────────────────────────────────
# 3. POLICY CONTEXT STRING (injected into every agent prompt)
# ─────────────────────────────────────────────────────────────────────────────

POLICY_CONTEXT = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAKSHA COMPANY POLICY — BINDING ON ALL AGENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RETURNS
• Window: {RETURN_POLICY.window_days} days after delivery.
• Order must be in 'delivered' status.
• Excluded categories: {', '.join(RETURN_POLICY.excluded_categories)}.
• Items discounted >50% are final sale — no returns.
• Original tags must be attached; item must be unworn.
• Maximum 1 return request per order.

EXCHANGES
• Window: {EXCHANGE_POLICY.window_days} days after delivery.
• Allowed reasons: {', '.join(EXCHANGE_POLICY.allowed_reasons)}.
• Maximum 1 exchange per order.

OFFERS & DISCOUNTS
• Max discount agent can generate (by loyalty tier):
  Bronze={OFFER_POLICY.max_discount_pct['bronze']}%  Silver={OFFER_POLICY.max_discount_pct['silver']}%  Gold={OFFER_POLICY.max_discount_pct['gold']}%  Platinum={OFFER_POLICY.max_discount_pct['platinum']}%
• Minimum cart value for offer: ₹{OFFER_POLICY.min_cart_value_for_offer:.0f}.
• Absolute maximum flat discount: ₹{OFFER_POLICY.max_flat_discount:.0f}.
• Personalized offers expire in {OFFER_POLICY.offer_expiry_hours}h.
• Maximum {OFFER_POLICY.max_active_offers_per_user} active offers per user — do not generate more.
• NEVER promise a discount beyond these limits.

LOYALTY POINTS
• Earn: ₹10 spent = 1 point.
• Redeem: 100 points = ₹10 off.
• Minimum cart ₹{LOYALTY_POLICY.min_cart_for_redemption:.0f} to redeem.
• Loyalty can cover at most {int(LOYALTY_POLICY.max_redemption_pct_of_cart*100)}% of cart value.
• Points expire after {LOYALTY_POLICY.points_expiry_days} days.

CANCELLATIONS
• Free cancellation before order reaches 'packed' status.
• ₹{CANCEL_POLICY.fee_after_packed:.0f} fee once packed.
• Cannot cancel after 'shipped'. Offer return instead.

DELIVERY
• Standard: {DELIVERY_POLICY.standard_sla_days[0]}–{DELIVERY_POLICY.standard_sla_days[1]} business days. Express: {DELIVERY_POLICY.express_sla_days[1]} business day.
• Reschedule must be requested ≥{DELIVERY_POLICY.reschedule_cutoff_hours}h before delivery window.
• Maximum {DELIVERY_POLICY.max_reschedule_attempts} reschedules per order.

PAYMENTS
• Max retries: {PAYMENT_POLICY.max_payment_retry_attempts}. After that, offer alternate method.
• COD only for orders ≤₹{PAYMENT_POLICY.cod_max_order_value:.0f}.
• Loyalty points can cover max {int(PAYMENT_POLICY.loyalty_points_max_contribution_pct*100)}% of order total.

HUMAN HANDOFF — MANDATORY TRIGGERS
• Agent failure ≥{HANDOFF_POLICY.max_agent_failures_before_handoff} times in a session.
• User says any of: {', '.join(f'"{k}"' for k in HANDOFF_POLICY.trigger_keywords[:4])} etc.
• Payment failure ≥{HANDOFF_POLICY.payment_failures_before_escalate} times.
• Complaint severity = '{HANDOFF_POLICY.complaint_severity_auto_escalate}'.
• When in doubt — escalate. Never argue with an upset customer.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# 4. PROMPT FACTORY — used by every agent
# ─────────────────────────────────────────────────────────────────────────────

def build_agent_prompt(
    agent_role: str,
    agent_instructions: str,
    extra_context: Optional[str] = None,
) -> str:
    """
    Builds the full system prompt for an agent by combining:
      - The company policy (always first)
      - The agent's role & specific instructions
      - Optional extra context (e.g. user summary, session state)

    Usage:
        SYSTEM_PROMPT = build_agent_prompt(
            agent_role="Offer Agent",
            agent_instructions="Your job is to...",
            extra_context="User loyalty tier: {loyalty_tier}"
        )
    """
    parts = [
        f"You are the {agent_role} for DAKSHA Fashion.",
        "",
        POLICY_CONTEXT,
        "",
        "YOUR SPECIFIC ROLE & INSTRUCTIONS",
        "=" * 40,
        agent_instructions,
    ]
    if extra_context:
        parts += ["", "ADDITIONAL CONTEXT", "=" * 40, extra_context]

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# 5. POLICY VALIDATORS — call these inside tool functions
# ─────────────────────────────────────────────────────────────────────────────

def validate_return_eligibility(
    order_status: str,
    days_since_delivery: int,
    category: str,
    discount_pct: float,
    has_tags: bool,
) -> tuple[bool, str]:
    """Returns (is_eligible, reason_if_not)."""
    p = RETURN_POLICY
    if order_status not in p.allowed_statuses:
        return False, f"Order must be in 'delivered' status to initiate a return."
    if days_since_delivery > p.window_days:
        return False, f"Return window of {p.window_days} days has passed."
    if category.lower() in p.excluded_categories:
        return False, f"'{category}' items are non-returnable."
    if discount_pct > p.excluded_if_discount_above_pct:
        return False, "Items purchased at >50% discount are final sale."
    if p.requires_tags and not has_tags:
        return False, "Original tags must be attached for a return."
    return True, ""


def cap_offer_discount(discount_pct: float, loyalty_tier: Optional[str]) -> float:
    """Clamps offer discount to policy maximum for the user's tier."""
    tier_key = (loyalty_tier or "default").lower()
    max_pct = OFFER_POLICY.max_discount_pct.get(tier_key, OFFER_POLICY.max_discount_pct["default"])
    return min(discount_pct, max_pct)


def validate_cancellation(order_status: str) -> tuple[bool, float, str]:
    """Returns (can_cancel, fee_amount, message)."""
    p = CANCEL_POLICY
    status_order = ["created", "confirmed", "packed", "shipped", "delivered"]
    try:
        idx = status_order.index(order_status)
        packed_idx = status_order.index("packed")
        shipped_idx = status_order.index("shipped")
    except ValueError:
        return False, 0.0, "Unknown order status."

    if idx >= shipped_idx:
        return False, 0.0, "Cannot cancel after shipment. Please initiate a return instead."
    if idx >= packed_idx:
        return True, p.fee_after_packed, f"A ₹{p.fee_after_packed:.0f} cancellation fee applies as the order is already packed."
    return True, 0.0, "Order cancelled successfully. No fee applies."


def validate_loyalty_redemption(
    points_to_redeem: int,
    cart_total: float,
    loyalty_tier: Optional[str] = None,
) -> tuple[bool, str]:
    p = LOYALTY_POLICY
    if cart_total < p.min_cart_for_redemption:
        return False, f"Minimum cart value of ₹{p.min_cart_for_redemption:.0f} required to redeem points."
    if points_to_redeem < p.min_points_to_redeem:
        return False, f"Minimum {p.min_points_to_redeem} points required for redemption."
    max_points_value = cart_total * p.max_redemption_pct_of_cart
    points_value = (points_to_redeem / 100) * p.rupees_per_100_points
    if points_value > max_points_value:
        allowed_points = int((max_points_value / p.rupees_per_100_points) * 100)
        return False, f"You can redeem at most {allowed_points} points on this order (20% of cart value)."
    return True, ""


# -----------------------------------------------------------------------------
# 6. POLICY DECISION LOGGER
# -----------------------------------------------------------------------------

import uuid as _uuid
import logging as _plog

_plogger = _plog.getLogger(__name__)


def log_policy_decision(
    db,
    *,
    rule_name,
    rule_category,
    agent_name,
    input_value=None,
    applied_value=None,
    was_overridden=False,
    session_id=None,
    user_id=None,
    agent_run_id=None,
    agent_action_id=None,
):
    """
    Write a PolicyDecision audit row. Safe to call from any tool function.
    Failures are swallowed so they never break the calling tool.
    """
    try:
        from app.models.models import PolicyDecision  # late import avoids circular dep

        def _su(v):
            if v is None:
                return None
            try:
                return _uuid.UUID(str(v))
            except (ValueError, AttributeError):
                return None

        record = PolicyDecision(
            session_id=_su(session_id),
            user_id=_su(user_id),
            agent_run_id=_su(agent_run_id),
            agent_action_id=_su(agent_action_id),
            agent_name=agent_name,
            rule_name=rule_name,
            rule_category=rule_category,
            input_value=input_value,
            applied_value=applied_value,
            was_overridden=was_overridden,
        )
        db.add(record)
        db.flush()
    except Exception as e:
        _plogger.warning(f"PolicyDecision log failed ({rule_name}): {e}")

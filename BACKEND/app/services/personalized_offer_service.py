# app/services/personalized_offer_service.py
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import (
    UserPersonalizedOffer,
    User,
    UserBehaviorAggregate,
)
from app.enums.db_enums import CouponTypeEnum
from app.services.loyalty_service import get_balance


def generate_dynamic_offer(db: Session, user_id, agent_run_id=None, requested_pct: float | None = None):
    """
    Create (or return the live) personalised offer for a user.

    Hard limits come from company_policy.OFFER_POLICY and are enforced HERE,
    not in a prompt: tier-based max percentage, absolute flat ceiling, expiry
    and the cap on concurrently active offers.
    """
    from app.ai.policy.company_policy import OFFER_POLICY, cap_offer_discount

    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    behavior = db.get(UserBehaviorAggregate, user_id)
    balance = get_balance(db, user_id)
    now = datetime.utcnow()

    active = (db.query(UserPersonalizedOffer)
              .filter(UserPersonalizedOffer.user_id == user_id,
                      UserPersonalizedOffer.is_redeemed == False,  # noqa: E712
                      UserPersonalizedOffer.expires_at > now)
              .order_by(desc(UserPersonalizedOffer.created_at)).all())
    if active:
        return active[0]          # never stack offers

    tier = (user.loyalty_tier or "bronze").lower()
    if balance > 1000:
        discount_val, discount_type, reason = 5, CouponTypeEnum.percentage, "Loyalty Reward"
    elif behavior and behavior.avg_viewed_price and behavior.avg_viewed_price > 5000:
        discount_val, discount_type, reason = 500, CouponTypeEnum.flat, "High Value Customer"
    else:
        discount_val, discount_type, reason = 10, CouponTypeEnum.percentage, "Special Offer"
    if requested_pct is not None and discount_type == CouponTypeEnum.percentage:
        discount_val = requested_pct

    if discount_type == CouponTypeEnum.percentage:
        discount_val = cap_offer_discount(float(discount_val), tier)
        label = f"{discount_val:g}% OFF"
    else:
        discount_val = min(float(discount_val), OFFER_POLICY.max_flat_discount)
        label = f"₹{discount_val:.0f} OFF"

    offer = UserPersonalizedOffer(
        id=uuid.uuid4(),
        user_id=user_id,
        agent_run_id=agent_run_id,
        offer_name=f"{reason}: {label}",
        discount_type=discount_type,
        discount_value=discount_val,
        condition_text=f"Valid for {OFFER_POLICY.offer_expiry_hours} hours on orders above ₹{OFFER_POLICY.min_cart_value_for_offer:.0f}",
        expires_at=now + timedelta(hours=OFFER_POLICY.offer_expiry_hours),
        is_redeemed=False,
    )
    db.add(offer)
    db.commit()
    return offer


def get_active_personal_offers(db: Session, user_id):
    return db.query(UserPersonalizedOffer).filter(
        UserPersonalizedOffer.user_id == user_id,
        UserPersonalizedOffer.is_redeemed == False,
        UserPersonalizedOffer.expires_at > datetime.utcnow(),
    ).all()
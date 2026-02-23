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


def generate_dynamic_offer(db: Session, user_id, agent_run_id=None):
    user = db.get(User, user_id)
    behavior = db.get(UserBehaviorAggregate, user_id)
    balance = get_balance(db, user_id)

    # prevent stacking
    active = db.query(UserPersonalizedOffer).filter(
        UserPersonalizedOffer.user_id == user_id,
        UserPersonalizedOffer.is_redeemed == False,
        UserPersonalizedOffer.expires_at > datetime.utcnow()
    ).first()

    if active:
        return active

    # RULE ENGINE
    if balance > 1000:
        discount_val = 5
        discount_type = CouponTypeEnum.percentage
        reason = "Loyalty Reward"

    elif behavior and behavior.avg_viewed_price and behavior.avg_viewed_price > 5000:
        discount_val = 500
        discount_type = CouponTypeEnum.flat
        reason = "High Value Customer"

    else:
        discount_val = 10
        discount_type = CouponTypeEnum.percentage
        reason = "Special Offer"

    if discount_type == CouponTypeEnum.percentage:
        label = f"{discount_val}% OFF"
    else:
        label = f"₹{discount_val} OFF"

    offer = UserPersonalizedOffer(
        id=uuid.uuid4(),
        user_id=user_id,
        agent_run_id=agent_run_id,
        offer_name=f"{reason}: {label}",
        discount_type=discount_type,
        discount_value=discount_val,
        condition_text="Valid for 1 hour",
        expires_at=datetime.utcnow() + timedelta(hours=1),
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
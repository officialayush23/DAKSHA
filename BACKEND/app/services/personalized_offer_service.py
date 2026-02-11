# app/services/personalized_offer_service.py
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    UserPersonalizedOffer, 
    User, 
    UserBehaviorAggregate, 
    RecommendationImpression
)
from app.enums.db_enums import CouponTypeEnum
from app.services.loyalty_service import calculate_user_balance

def generate_dynamic_offer(db: Session, user_id, agent_run_id=None):
    """
    Agent calls this to create a 'Flash Sale' for the user.
    Rules:
    1. High Loyalty Balance -> Small nudge (5%)
    2. Cart Abandoner -> Medium nudge (10%)
    3. New User -> Welcome Offer
    """
    user = db.query(User).get(user_id)
    behavior = db.query(UserBehaviorAggregate).get(user_id)
    balance = calculate_user_balance(db, user_id)

    # --- RULE ENGINE ---
    discount_val = 0
    reason = ""

    if balance > 1000:
        # High loyalty, just needs a small nudge
        discount_val = 5
        reason = "Loyalty Reward"
    elif behavior and behavior.avg_viewed_price and behavior.avg_viewed_price > 5000:
        # High spender, give flat discount
        discount_val = 500
        reason = "High Value Customer"
        discount_type = CouponTypeEnum.flat
    else:
        # Default fallback
        discount_val = 10
        reason = "Special Offer"
        discount_type = CouponTypeEnum.percentage

    # Check cooldown (Don't spam offers)
    last_offer = db.query(UserPersonalizedOffer)\
        .filter(UserPersonalizedOffer.user_id == user_id)\
        .order_by(desc(UserPersonalizedOffer.created_at))\
        .first()

    if last_offer and last_offer.created_at > datetime.utcnow() - timedelta(hours=24):
        return None # Too soon

    # Create Offer
    offer = UserPersonalizedOffer(
        id=uuid.uuid4(),
        user_id=user_id,
        agent_run_id=agent_run_id,
        offer_name=f"{reason}: Get {discount_val}% OFF",
        discount_type=discount_type if 'discount_type' in locals() else CouponTypeEnum.percentage,
        discount_value=discount_val,
        condition_text="Valid for next 1 hour only",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_redeemed=False
    )
    db.add(offer)
    db.commit()
    return offer

def get_active_personal_offers(db: Session, user_id):
    """
    Fetch valid offers for checkout application.
    """
    return db.query(UserPersonalizedOffer).filter(
        UserPersonalizedOffer.user_id == user_id,
        UserPersonalizedOffer.is_redeemed == False,
        UserPersonalizedOffer.expires_at > datetime.utcnow()
    ).all()
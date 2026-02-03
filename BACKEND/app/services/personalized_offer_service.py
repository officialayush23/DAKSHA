# app/services/personalized_offer_service.py
from sqlalchemy.orm import Session
from app.models.models import Offer, User, RecommendationImpression
from datetime import datetime, timedelta

def get_personalized_offer(
    db: Session,
    user_id,
    variant_id,
):
    """
    Returns a personalized offer if user is eligible.
    Used ONLY by agent or checkout recovery.
    """

    user = db.query(User).get(user_id)
    if not user:
        return None

    # 1. Loyalty gating
    if user.loyalty_tier not in ("gold", "platinum"):
        return None

    # 2. Has user seen this item recently?
    recent = db.query(RecommendationImpression).filter(
        RecommendationImpression.user_id == user_id,
        RecommendationImpression.product_variant_id == variant_id,
        RecommendationImpression.created_at > datetime.utcnow() - timedelta(days=7)
    ).count()

    if recent < 2:
        return None

    # 3. Fetch eligible personal offer
    offer = db.query(Offer).filter(
        Offer.personalized == True,
        Offer.active == True,
        Offer.valid_to >= datetime.utcnow()
    ).order_by(Offer.discount_value.desc()).first()

    if not offer:
        return None

    return {
        "id": str(offer.id),
        "label": f"Special for you: {offer.discount_value}% OFF",
        "type": "personalized"
    }

# app/services/agent_coupon_service.py
from sqlalchemy.orm import Session
from app.models.models import Coupon, UserPersonalizedOffer


def list_all_coupons(db: Session):
    return {
        "global": db.query(Coupon).all(),
        "personalized": db.query(UserPersonalizedOffer).all(),
    }

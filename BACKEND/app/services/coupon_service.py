# app/services/coupon_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import List, Dict
from app.models.models import (
    CheckoutSession,
    Coupon,
    UserPersonalizedOffer,
    CouponRedemption,
)
from app.services.personalized_offer_service import get_active_personal_offers

def get_eligible_coupons(db: Session, user_id, cart_total: float, category_set: set[str]):
    """Returns eligible coupons. Personalized offers ALWAYS first."""
    now = datetime.utcnow()
    personalized = get_active_personal_offers(db, user_id)

    rows = db.execute(text("""
        SELECT *
        FROM coupons
        WHERE status = 'active'
        AND valid_from <= :now
        AND (valid_to IS NULL OR valid_to >= :now)
        AND (min_order_value IS NULL OR min_order_value <= :total)
    """), {"now": now, "total": cart_total}).fetchall()

    eligible = []
    for r in rows:
        if r.scope == "all":
            eligible.append(r)
        elif r.scope == "category" and r.scope_value in category_set:
            eligible.append(r)
        elif r.scope == "product":
            eligible.append(r)

    return {
        "personalized": personalized,
        "system": eligible,
    }

def apply_coupon(
    db: Session,
    checkout_id,
    coupon_code: str | None = None,
    personal_offer_id=None,
    cart_total: float = 0,
):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise ValueError("Checkout session not found.")

    if personal_offer_id:
        offer = db.get(UserPersonalizedOffer, personal_offer_id)
        
        # 👇 NEW: Safety check to prevent NoneType Error
        if not offer:
            raise ValueError("Personalized offer not found or invalid.")

        discount = (
            cart_total * float(offer.discount_value) / 100
            if offer.discount_type == "percentage"
            else float(offer.discount_value)
        )

        checkout.applied_personal_offer_id = offer.id
        checkout.discount_amount = discount

    elif coupon_code:
        coupon = db.query(Coupon).filter_by(code=coupon_code).first()
        
        # 👇 NEW: Safety check to prevent NoneType Error
        if not coupon:
            raise ValueError(f"Coupon code '{coupon_code}' not found or invalid.")

        discount = (
            cart_total * float(coupon.value) / 100
            if coupon.coupon_type == "percentage"
            else float(coupon.value)
        )

        if coupon.max_discount:
            discount = min(discount, float(coupon.max_discount))

        checkout.applied_coupon_id = coupon.id
        checkout.discount_amount = discount

    db.commit()
    return checkout.discount_amount


def finalize_coupon_redemption(db: Session, checkout_id, order_id):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        return

    if checkout.applied_coupon_id:
        redemption = CouponRedemption(
            coupon_id=checkout.applied_coupon_id,
            order_id=order_id,
            user_id=checkout.user_id,
        )
        db.add(redemption)

    if checkout.applied_personal_offer_id:
        offer = db.get(UserPersonalizedOffer, checkout.applied_personal_offer_id)
        if offer:
            offer.is_redeemed = True
            offer.redeemed_order_id = order_id

    db.commit()
# app/services/coupon_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import List, Dict
from app.models.models import (
    CheckoutSession,
    Coupon,
    UserPersonalizedOffer,
)

from app.models.models import (
    CheckoutSession,
    CouponRedemption,
    UserPersonalizedOffer,
)

from app.services.personalized_offer_service import get_active_personal_offers

# gives eligible coupons for a user based on cart total and categories. Personalized offers are always returned first.
def get_eligible_coupons(
    db: Session,
    user_id,
    cart_total: float,
    category_set: set[str],
):
    """
    Returns eligible coupons.
    Personalized offers ALWAYS first.
    """

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
        if r.scope == "global":
            eligible.append(r)
        elif r.scope == "category" and r.scope_value in category_set:
            eligible.append(r)
        elif r.scope == "product":
            eligible.append(r)

    return {
        "personalized": personalized,
        "system": eligible,
    }
    
    
    

# coupon application logic - applies either a personalized offer or a system coupon to the checkout session. Returns the discount amount.
def apply_coupon(
    db: Session,
    checkout_id,
    coupon_code: str | None = None,
    personal_offer_id=None,
    cart_total: float = 0,
):
    checkout = db.get(CheckoutSession, checkout_id)

    if personal_offer_id:
        offer = db.get(UserPersonalizedOffer, personal_offer_id)

        discount = (
            cart_total * offer.discount_value / 100
            if offer.discount_type == "percentage"
            else offer.discount_value
        )

        checkout.applied_personal_offer_id = offer.id
        checkout.discount_amount = discount

    elif coupon_code:
        coupon = db.query(Coupon).filter_by(code=coupon_code).first()

        discount = (
            cart_total * coupon.value / 100
            if coupon.coupon_type == "percentage"
            else coupon.value
        )

        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)

        checkout.applied_coupon_id = coupon.id
        checkout.discount_amount = discount

    db.commit()

    return checkout.discount_amount



# finalizes the coupon redemption by creating a CouponRedemption record and marking the personalized offer as redeemed if applicable. Called after successful order placement.

def finalize_coupon_redemption(db: Session, checkout_id, order_id):
    checkout = db.get(CheckoutSession, checkout_id)

    if checkout.applied_coupon_id:
        redemption = CouponRedemption(
            coupon_id=checkout.applied_coupon_id,
            order_id=order_id,
            user_id=checkout.user_id,
        )
        db.add(redemption)

    if checkout.applied_personal_offer_id:
        offer = db.get(UserPersonalizedOffer,
                       checkout.applied_personal_offer_id)
        offer.is_redeemed = True
        offer.redeemed_order_id = order_id

    db.commit()
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

    # Use .mappings() to get dictionary-like row access
    rows = db.execute(text("""
        SELECT *
        FROM coupons
        WHERE status = 'active'
        AND valid_from <= :now
        AND (valid_to IS NULL OR valid_to >= :now)
        AND (min_order_value IS NULL OR min_order_value <= :total)
    """), {"now": now, "total": cart_total}).mappings().fetchall()

    eligible = []
    for r in rows:
        # 🛠️ FIXED: Convert SQLAlchemy RowMapping to a standard Python dictionary
        coupon_dict = dict(r)
        
        # Safely cast UUIDs and Decimals to strings and floats for JSON
        coupon_dict["id"] = str(coupon_dict["id"])
        if coupon_dict.get("value"): coupon_dict["value"] = float(coupon_dict["value"])
        if coupon_dict.get("min_order_value"): coupon_dict["min_order_value"] = float(coupon_dict["min_order_value"])
        if coupon_dict.get("max_discount"): coupon_dict["max_discount"] = float(coupon_dict["max_discount"])
        if coupon_dict.get("valid_from"): coupon_dict["valid_from"] = coupon_dict["valid_from"].isoformat()
        if coupon_dict.get("valid_to"): coupon_dict["valid_to"] = coupon_dict["valid_to"].isoformat()
        if coupon_dict.get("created_at"): coupon_dict["created_at"] = coupon_dict["created_at"].isoformat()

        if r["scope"] == "all":
            eligible.append(coupon_dict)
        elif r["scope"] == "category" and r["scope_value"] in category_set:
            eligible.append(coupon_dict)
        elif r["scope"] == "product":
            eligible.append(coupon_dict)

    # 🛠️ FIXED: Serialize personalized offers safely
    serialized_personalized = []
    for p in personalized:
        serialized_personalized.append({
            "id": str(p.id),
            "offer_name": p.offer_name,
            "discount_type": p.discount_type.value if hasattr(p.discount_type, 'value') else p.discount_type,
            "discount_value": float(p.discount_value),
            "condition_text": p.condition_text,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None
        })

    return {
        "personalized": serialized_personalized,
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
        
        # 🛡️ SAFETY CHECK to prevent NoneType Error
        if not offer:
            raise ValueError("Personalized offer not found or invalid.")

        discount = (
            cart_total * float(offer.discount_value) / 100
            if getattr(offer.discount_type, 'value', offer.discount_type) == "percentage"
            else float(offer.discount_value)
        )

        checkout.applied_personal_offer_id = offer.id
        checkout.applied_coupon_id = None # Clear system coupon if applying personal
        checkout.discount_amount = discount

    elif coupon_code:
        coupon = db.query(Coupon).filter_by(code=coupon_code).first()
        
        # 🛡️ SAFETY CHECK to prevent NoneType Error
        if not coupon:
            raise ValueError(f"Coupon code '{coupon_code}' not found or invalid.")

        discount = (
            cart_total * float(coupon.value) / 100
            if getattr(coupon.coupon_type, 'value', coupon.coupon_type) == "percentage"
            else float(coupon.value)
        )

        if coupon.max_discount:
            discount = min(discount, float(coupon.max_discount))

        checkout.applied_coupon_id = coupon.id
        checkout.applied_personal_offer_id = None # Clear personal offer if applying system coupon
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
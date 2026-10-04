# app/services/coupon_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, timezone
from uuid import UUID
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
    now = datetime.now(timezone.utc)
    personalized = get_active_personal_offers(db, user_id)

    # Use .mappings() to get dictionary-like row access
    rows = db.execute(text("""
        SELECT *
        FROM coupons
        WHERE status = 'active'
        AND (valid_from IS NULL OR valid_from <= :now)
        AND (valid_to IS NULL OR valid_to >= :now)
        AND (min_order_value IS NULL OR min_order_value <= :total)
    """), {"now": now, "total": cart_total}).mappings().fetchall()

    eligible = []
    for r in rows:
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

def _clean(v):
    if isinstance(v, str):
        v = v.strip()
        if v.lower() in ("", "null", "undefined", "none"):
            return None
    return v


def _aware(dt):
    return dt if (dt is None or dt.tzinfo) else dt.replace(tzinfo=timezone.utc)


def apply_coupon(
    db: Session,
    checkout_id,
    coupon_code: str | None = None,
    personal_offer_id=None,
    cart_total: float | None = None,   # ignored: kept for old callers; the server price is used
    user_id=None,
):
    """
    Apply a coupon OR a personalised offer to a checkout.

    The discount is always computed from checkout.locked_price, which the
    server locked when stock was reserved. A caller (UI or agent) cannot
    inflate the base by passing its own cart_total.
    """
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout or (user_id is not None and str(checkout.user_id) != str(user_id)):
        raise ValueError("Checkout session not found.")
    if getattr(checkout.state, "value", checkout.state) in ("ORDER_CONFIRMED", "CANCELLED", "ROLLED_BACK"):
        raise ValueError("This checkout is closed. Start a new checkout to use a coupon.")

    base = float(checkout.locked_price or 0)
    personal_offer_id = _clean(personal_offer_id)
    coupon_code = _clean(coupon_code)
    now = datetime.now(timezone.utc)

    if not personal_offer_id and not coupon_code:
        checkout.applied_personal_offer_id = None
        checkout.applied_coupon_id = None
        checkout.discount_amount = 0
        db.commit()
        return 0

    if personal_offer_id:
        try:
            valid_uuid = UUID(str(personal_offer_id))
        except ValueError:
            raise ValueError("Invalid personalized offer ID format.")
        offer = db.get(UserPersonalizedOffer, valid_uuid)
        if not offer:
            raise ValueError("Personalized offer not found.")
        if offer.user_id != checkout.user_id:
            raise ValueError("This offer belongs to a different user.")
        if offer.is_redeemed:
            raise ValueError("This offer has already been redeemed.")
        if offer.expires_at and _aware(offer.expires_at) < now:
            raise ValueError("This offer has expired.")
        pct = getattr(offer.discount_type, "value", offer.discount_type) == "percentage"
        discount = base * float(offer.discount_value) / 100 if pct else float(offer.discount_value)
        checkout.applied_personal_offer_id = offer.id
        checkout.applied_coupon_id = None
    else:
        coupon = db.query(Coupon).filter(func.upper(Coupon.code) == coupon_code.upper()).first()
        if not coupon or getattr(coupon.status, "value", coupon.status) != "active":
            raise ValueError(f"Coupon code '{coupon_code}' is invalid or inactive.")
        if coupon.valid_from and _aware(coupon.valid_from) > now:
            raise ValueError("This coupon is not active yet.")
        if coupon.valid_to and _aware(coupon.valid_to) < now:
            raise ValueError("This coupon has expired.")
        if coupon.min_order_value and base < float(coupon.min_order_value):
            raise ValueError(f"This coupon needs a minimum order of {float(coupon.min_order_value):.0f}.")
        used = db.query(func.count(CouponRedemption.id)).filter(CouponRedemption.coupon_id == coupon.id).scalar() or 0
        if coupon.usage_limit and used >= coupon.usage_limit:
            raise ValueError("This coupon has reached its usage limit.")
        mine = (db.query(func.count(CouponRedemption.id))
                .filter(CouponRedemption.coupon_id == coupon.id, CouponRedemption.user_id == checkout.user_id).scalar() or 0)
        if coupon.per_user_limit and mine >= coupon.per_user_limit:
            raise ValueError("You've already used this coupon.")
        scope = getattr(coupon.scope, "value", coupon.scope)
        if scope == "category" and coupon.scope_value:
            hit = db.execute(text("""SELECT 1 FROM cart_items ci JOIN product_variants pv ON pv.id = ci.product_variant_id
                                     JOIN products p ON p.id = pv.product_id
                                     WHERE ci.cart_id = :c AND (lower(p.category) = lower(:v) OR lower(p.brand) = lower(:v)) LIMIT 1"""),
                             {"c": str(checkout.cart_id), "v": coupon.scope_value}).first()
            if not hit:
                raise ValueError(f"'{coupon.code}' only applies to {coupon.scope_value} items.")
        pct = getattr(coupon.coupon_type, "value", coupon.coupon_type) == "percentage"
        discount = base * float(coupon.value) / 100 if pct else float(coupon.value)
        if coupon.max_discount:
            discount = min(discount, float(coupon.max_discount))
        checkout.applied_coupon_id = coupon.id
        checkout.applied_personal_offer_id = None

    checkout.discount_amount = round(max(0.0, min(discount, base)), 2)
    db.commit()
    return float(checkout.discount_amount)


def finalize_coupon_redemption(db: Session, checkout_id, order_id):
    """
    Called ONLY when the payment is successful and order is confirmed.
    This safely executes the actual consumption of the offer.
    """
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        return

    # Handle standard coupon
    if checkout.applied_coupon_id:
        redemption = CouponRedemption(
            coupon_id=checkout.applied_coupon_id,
            order_id=order_id,
            user_id=checkout.user_id,
        )
        db.add(redemption)

    # Handle Personalized Offers (Mark as redeemed so it can't be used again)
    if checkout.applied_personal_offer_id:
        offer = db.get(UserPersonalizedOffer, checkout.applied_personal_offer_id)
        if offer:
            offer.is_redeemed = True
            offer.redeemed_order_id = order_id

    db.commit()
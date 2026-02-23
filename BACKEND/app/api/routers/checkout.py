# app/api/routers/checkout.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.deps import get_db
from app.models.models import CheckoutSession
from app.enums.db_enums import FulfillmentTypeEnum

from app.services.checkout_service import initialize_checkout, finalize_checkout
from app.services.coupon_service import apply_coupon, get_eligible_coupons
from app.services.store_availability_service import get_nearest_stores_with_cart

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post("/start")
def start_checkout(user_id: UUID, session_id: UUID, cart_id: UUID, db: Session = Depends(get_db)):
    return initialize_checkout(db, user_id, session_id, cart_id)


@router.get("/{checkout_id}/stores")
def eligible_stores(checkout_id: UUID, lat: float, lng: float, db: Session = Depends(get_db)):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise HTTPException(404, "Checkout not found")

    return get_nearest_stores_with_cart(
        db,
        cart_id=checkout.cart_id,
        user_lat=lat,
        user_lng=lng
    )


@router.get("/{checkout_id}/coupons")
def coupons(checkout_id: UUID, db: Session = Depends(get_db)):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise HTTPException(404, "Checkout not found")

    return get_eligible_coupons(
        db,
        checkout.user_id,
        checkout.locked_price,
        set()
    )


@router.post("/{checkout_id}/apply-coupon")
def apply_coupon_route(
    checkout_id: UUID,
    coupon_code: str | None = None,
    offer_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise HTTPException(404, "Checkout not found")

    return apply_coupon(
        db,
        checkout_id,
        coupon_code,
        offer_id,
        checkout.locked_price,
    )


@router.post("/{checkout_id}/finalize")
def finalize_checkout_route(
    checkout_id: UUID,
    fulfillment_type: FulfillmentTypeEnum,
    store_id: UUID | None = None,
    delivery_address_id: UUID | None = None,
    scheduled_time: str | None = None,
    redeem_loyalty_points: int = 0,
    db: Session = Depends(get_db),
):
    return finalize_checkout(
        db,
        checkout_id=checkout_id,
        fulfillment_type=fulfillment_type,
        store_id=store_id,
        delivery_address_id=delivery_address_id,
        scheduled_time=scheduled_time,
        redeem_loyalty_points=redeem_loyalty_points,
    )
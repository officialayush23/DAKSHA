# app/api/routers/checkout.py
"""
Checkout (UI path). Every route is authenticated and scoped to the caller:
the user comes from the token, never from the request body, and checkouts or
carts that belong to someone else return 404.
"""
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, get_channel
from app.enums.db_enums import ChannelEnum, FulfillmentTypeEnum
from app.models.models import CheckoutSession, UserAddress
from app.schemas.schemas import (
    AddressResponse, ApplyCouponPayload, DeliveryCheckoutRequest, FinalizeCheckoutRequest, PickupCheckoutRequest,
)
from app.services.checkout_service import create_checkout_after_fulfillment, finalize_checkout
from app.services.coupon_service import apply_coupon, get_eligible_coupons
from app.services.store_availability_service import get_nearest_stores_with_cart

router = APIRouter(prefix="/checkout", tags=["Checkout"])


def _mine(db: Session, checkout_id: UUID, user) -> CheckoutSession:
    co = db.get(CheckoutSession, checkout_id)
    if not co or co.user_id != user.id:
        raise HTTPException(404, "Checkout not found")
    return co


def _session_for(db: Session, user, requested, channel):
    from app.agentic.commerce.context import ensure_web_session
    return ensure_web_session(db, user.id, getattr(channel, "value", channel) or "web").id


def _ch(channel) -> ChannelEnum:
    if isinstance(channel, ChannelEnum):
        return channel
    try:
        return ChannelEnum({"pwa": "app"}.get(str(channel), str(channel)))
    except ValueError:
        return ChannelEnum.web


@router.post("/delivery")
def start_delivery_checkout(payload: DeliveryCheckoutRequest, db: Session = Depends(get_db),
                            user=Depends(get_current_user), channel: ChannelEnum = Depends(get_channel)):
    try:
        co = create_checkout_after_fulfillment(
            db=db, user_id=user.id, session_id=_session_for(db, user, payload.session_id, channel),
            cart_id=payload.cart_id, fulfillment_type=FulfillmentTypeEnum.delivery, channel=_ch(channel))
        return {"checkout_id": co.id, "locked_price": co.locked_price, "reserved_until": co.reserved_until}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{checkout_id}/addresses", response_model=List[AddressResponse])
def get_checkout_addresses(checkout_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _mine(db, checkout_id, user)
    return db.query(UserAddress).filter(UserAddress.user_id == user.id).all()


@router.get("/pickup/stores")
def pickup_stores(cart_id: UUID, lat: float, lng: float, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from app.models.models import Cart
    cart = db.get(Cart, cart_id)
    if not cart or cart.user_id != user.id:
        raise HTTPException(404, "Cart not found")
    return get_nearest_stores_with_cart(db, cart_id, lat, lng)


@router.post("/pickup")
def start_pickup_checkout(payload: PickupCheckoutRequest, db: Session = Depends(get_db),
                          user=Depends(get_current_user), channel: ChannelEnum = Depends(get_channel)):
    try:
        co = create_checkout_after_fulfillment(
            db=db, user_id=user.id, session_id=_session_for(db, user, payload.session_id, channel),
            cart_id=payload.cart_id, fulfillment_type=FulfillmentTypeEnum.pickup, store_id=payload.store_id,
            channel=_ch(channel))
        return {"checkout_id": co.id, "locked_price": co.locked_price, "reserved_until": co.reserved_until}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{checkout_id}/coupons")
def coupons(checkout_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    co = _mine(db, checkout_id, user)
    return get_eligible_coupons(db, co.user_id, float(co.locked_price or 0), set())


@router.post("/{checkout_id}/apply-coupon")
def apply_coupon_route(checkout_id: UUID, payload: ApplyCouponPayload, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    _mine(db, checkout_id, user)
    try:
        discount = apply_coupon(db, checkout_id, coupon_code=payload.coupon_code,
                                personal_offer_id=payload.offer_id, user_id=user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "success", "discount_amount": discount}


@router.post("/{checkout_id}/finalize")
async def finalize_checkout_route(checkout_id: UUID, payload: FinalizeCheckoutRequest, db: Session = Depends(get_db),
                                  user=Depends(get_current_user)):
    _mine(db, checkout_id, user)
    try:
        parsed_time = None
        if payload.scheduled_time:
            parsed_time = datetime.fromisoformat(payload.scheduled_time.replace("Z", "+00:00"))
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=timezone.utc)
        result = await finalize_checkout(db=db, checkout_id=checkout_id, delivery_address_id=payload.delivery_address_id,
                                         scheduled_time=parsed_time, redeem_loyalty_points=payload.redeem_loyalty_points,
                                         user_id=user.id)
        if result.get("status") == "payment_failed":
            raise HTTPException(402, result.get("reason", "Payment Failed"))
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))

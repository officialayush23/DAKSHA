# app/api/routers/checkout.py
# app/api/routers/checkout.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from datetime import datetime, timezone # ⬅️ Imported for time parsing

from app.core.deps import get_db
from app.models.models import CheckoutSession, UserAddress
from app.enums.db_enums import FulfillmentTypeEnum

from app.schemas.schemas import (
    DeliveryCheckoutRequest, PickupCheckoutRequest, FinalizeCheckoutRequest, 
    ApplyCouponPayload, AddressResponse
)
from app.services.checkout_service import create_checkout_after_fulfillment, finalize_checkout
from app.services.coupon_service import apply_coupon, get_eligible_coupons
from app.services.store_availability_service import get_nearest_stores_with_cart

router = APIRouter(prefix="/checkout", tags=["Checkout"])

# 1️⃣ START DELIVERY CHECKOUT
@router.post("/delivery")
def start_delivery_checkout(payload: DeliveryCheckoutRequest, db: Session = Depends(get_db)):
    try:
        checkout = create_checkout_after_fulfillment(
            db=db,
            user_id=payload.user_id,
            session_id=payload.session_id,
            cart_id=payload.cart_id,
            fulfillment_type=FulfillmentTypeEnum.delivery,
        )
        return {"checkout_id": checkout.id, "locked_price": checkout.locked_price}
    except Exception as e:
        raise HTTPException(400, str(e))

# 2️⃣ GET ADDRESSES FOR DELIVERY CHECKOUT
@router.get("/{checkout_id}/addresses", response_model=List[AddressResponse])
def get_checkout_addresses(checkout_id: UUID, db: Session = Depends(get_db)):
    """Fetches the saved addresses for the user currently checking out."""
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise HTTPException(404, "Checkout not found")

    addresses = db.query(UserAddress).filter(UserAddress.user_id == checkout.user_id).all()
    return addresses

# 3️⃣ FIND PICKUP STORES
@router.get("/pickup/stores")
def pickup_stores(cart_id: UUID, lat: float, lng: float, db: Session = Depends(get_db)):
    return get_nearest_stores_with_cart(db, cart_id, lat, lng)

# 4️⃣ START PICKUP CHECKOUT (Store Selected)
@router.post("/pickup")
def start_pickup_checkout(payload: PickupCheckoutRequest, db: Session = Depends(get_db)):
    try:
        checkout = create_checkout_after_fulfillment(
            db=db,
            user_id=payload.user_id,
            session_id=payload.session_id,
            cart_id=payload.cart_id,
            fulfillment_type=FulfillmentTypeEnum.pickup,
            store_id=payload.store_id,
        )
        return {"checkout_id": checkout.id, "locked_price": checkout.locked_price}
    except Exception as e:
        raise HTTPException(400, str(e))

# 5️⃣ GET COUPONS
@router.get("/{checkout_id}/coupons")
def coupons(checkout_id: UUID, db: Session = Depends(get_db)):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise HTTPException(404, "Checkout not found")

    return get_eligible_coupons(db, checkout.user_id, checkout.locked_price, set())

# 6️⃣ APPLY COUPON
@router.post("/{checkout_id}/apply-coupon")
def apply_coupon_route(checkout_id: UUID, payload: ApplyCouponPayload, db: Session = Depends(get_db)):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise HTTPException(404, "Checkout not found")

    discount = apply_coupon(
        db, checkout_id, coupon_code=payload.coupon_code, 
        personal_offer_id=payload.offer_id, cart_total=checkout.locked_price
    )
    return {"status": "success", "discount_amount": discount}

# 7️⃣ FINALIZE (PAY)
@router.post("/{checkout_id}/finalize")
async def finalize_checkout_route(checkout_id: UUID, payload: FinalizeCheckoutRequest, db: Session = Depends(get_db)):
    try:
        parsed_time = None
        if payload.scheduled_time:
            parsed_time = datetime.fromisoformat(payload.scheduled_time.replace('Z', '+00:00'))
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=timezone.utc)

        # 👇 FIXED: Added await here
        result = await finalize_checkout(
            db=db,
            checkout_id=checkout_id,
            delivery_address_id=payload.delivery_address_id,
            scheduled_time=parsed_time, 
            redeem_loyalty_points=payload.redeem_loyalty_points,
        )
        if result.get("status") == "payment_failed":
            raise HTTPException(402, result.get("reason", "Payment Failed"))
            
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
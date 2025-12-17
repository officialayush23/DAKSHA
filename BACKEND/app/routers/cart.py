# app/routers/cart.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.commerce import AddToCartRequest, CheckoutRequest
from app.services.commerce_service import CommerceService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/add")
async def add_to_cart(
    payload: AddToCartRequest,
    user_id: str = Depends(get_current_user_id),
):
    return await CommerceService.add_to_cart(
        user_id=user_id,
        variant_id=payload.variant_id,
        fulfillment_location_id=payload.fulfillment_location_id,
        qty=payload.quantity,
    )


@router.get("")
async def get_cart(user_id: str = Depends(get_current_user_id)):
    return CommerceService.get_cart_snapshot(user_id) or {
        "cart": None,
        "items": [],
        "pricing": None,
        "fulfillment_preview": None,
    }


@router.post("/checkout/preview")
async def checkout_preview(
    payload: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
):
    return CommerceService.checkout_preview(
        user_id=user_id,
        order_type=payload.order_type,
        pickup_location_id=payload.pickup_fulfillment_location_id,
        address_id=payload.address_id,
        promotion_code=payload.promotion_code,
    )

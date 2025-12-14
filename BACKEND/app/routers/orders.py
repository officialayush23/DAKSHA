# app/routers/orders.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.core.auth import get_current_user_id
from app.models.commerce import ReturnRequest, CheckoutRequest
from app.database import supabase
from app.services.commerce_service import CommerceService

router = APIRouter(prefix="/orders", tags=["Orders"])


# ---------------------------------------------------------
# ORDER HISTORY
# ---------------------------------------------------------
@router.get("/history")
async def get_order_history(user_id: str = Depends(get_current_user_id)):
    """
    Includes order_items + product info + fulfillment locations.
    """
    res = (
        supabase.table("orders")
        .select(
            "*, "
            "order_items(*, product_variants(*, products(name)))"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


# ---------------------------------------------------------
# CHECKOUT
# ---------------------------------------------------------
@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Unified checkout handler:
    - Delivery (warehouse-first, nearest-store fallback)
    - Pickup (single-store strict)
    - Returns allocation map + agent_reason for chatbot
    """

    result = CommerceService.checkout(
        user_id=user_id,
        order_type=payload.order_type,
        store_pickup_location_id=payload.pickup_fulfillment_location_id,
        address_id=payload.address_id,
        promotion_code=payload.promotion_code,
    )

    return {
        "status": "success",
        "order": result["order"],
        "allocation": result["allocation"],
        "agent_reason": result["agent_reason"],
    }


# ---------------------------------------------------------
# RETURNS
# ---------------------------------------------------------
@router.post("/return")
async def initiate_return(
    req: ReturnRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Validates:
    - Order item belongs to user
    - Item is returnable
    - Creates a row in returns()
    """

    item_check = (
        supabase.table("order_items")
        .select("*, orders(user_id)")
        .eq("id", req.order_item_id)
        .eq("order_id", req.order_id)
        .single()
        .execute()
    ).data

    if not item_check:
        raise HTTPException(404, "Order item not found")

    if item_check["orders"]["user_id"] != user_id:
        raise HTTPException(403, "Unauthorized return attempt")

    if item_check.get("non_returnable"):
        raise HTTPException(400, "This item is marked non-returnable")

    refund_amt = item_check["price_at_purchase"]

    ins = (
        supabase.table("returns")
        .insert(
            {
                "order_id": req.order_id,
                "order_item_id": req.order_item_id,
                "type": req.type,
                "reason": req.reason,
                "refund_amount": refund_amt,
                "status": "requested",
            }
        )
        .execute()
    ).data[0]

    return {
        "status": "return_requested",
        "return_id": ins["id"],
    }

# app/routers/orders.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.core.auth import get_current_user_id
from app.schemas.schemas import ReturnRequest, CheckoutRequest
from app.core.database import supabase
from app.services.commerce_service import CommerceService

router = APIRouter(prefix="/orders", tags=["Orders"])


# ---------------------------------------------------------
# ORDER HISTORY
# ---------------------------------------------------------
@router.get("")
async def get_orders(
    user_id: str = Depends(get_current_user_id),
    limit: int = 20
):
    """Get user's orders (for Support page dropdown)"""
    try:
        orders = (
            supabase.table("orders")
            .select("id, total_amount, created_at, status, currency")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch orders: {str(e)}")


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

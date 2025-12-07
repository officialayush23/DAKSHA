from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.schemas import ReturnRequest, CheckoutRequest
from app.database import supabase
from app.services.commerce_service import CommerceService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/history")
async def get_order_history(user_id: str = Depends(get_current_user_id)):
    res = (
        supabase.table("orders")
        .select("*, order_items(*, product_variants(*, products(name)))")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
):
    order = CommerceService.checkout(
        user_id,
        payload.order_type,
        payload.store_id,
        payload.address_id,
        payload.promotion_code,
    )
    return {"order": order}


@router.post("/return")
async def initiate_return(
    req: ReturnRequest, user_id: str = Depends(get_current_user_id)
):
    item_check = (
        supabase.table("order_items")
        .select("*")
        .eq("id", req.order_item_id)
        .eq("order_id", req.order_id)
        .single()
        .execute()
    )

    if not item_check.data:
        raise HTTPException(404, "Order Item not found or mismatch")

    if item_check.data["non_returnable"]:
        raise HTTPException(400, "This item is non-returnable")

    refund_amt = item_check.data["price_at_purchase"]

    res = (
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
    )

    return {"status": "return_requested", "ticket_id": res.data[0]["id"]}

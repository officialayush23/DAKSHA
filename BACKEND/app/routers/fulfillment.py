# app/routers/fulfillment.py

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.core.database import supabase
from app.core.auth import get_current_user_id
from app.core.rbac import require_store_access, require_warehouse_access
from app.services.human_handoff_service import HumanHandoffService

router = APIRouter(prefix="/fulfillment", tags=["Fulfillment"])


@router.get("/list/{location_id}")
async def list_fulfillments(
    location_id: str,
    user_id: str = Depends(get_current_user_id),
):
    return (
        supabase.table("fulfillments")
        .select("*, orders(user_id, total_amount)")
        .eq("fulfillment_location_id", location_id)
        .order("created_at")
        .execute()
    ).data


@router.post("/{fulfillment_id}/pack")
async def mark_packed(
    fulfillment_id: str,
    _rbac = Depends(require_store_access("location_id")),
):
    f = supabase.table("fulfillments").select("*").eq("id", fulfillment_id).single().execute().data

    if f["status"] != "pending":
        raise HTTPException(409, "Only pending fulfillments can be packed")

    return (
        supabase.table("fulfillments")
        .update({
            "status": "packed",
            "packed_at": datetime.utcnow(),
        })
        .eq("id", fulfillment_id)
        .execute()
    ).data[0]

@router.post("/{fulfillment_id}/ship")
async def mark_shipped(
    fulfillment_id: str,
    tracking_number: str,
    carrier: str,
):
    f = supabase.table("fulfillments").select("*").eq("id", fulfillment_id).single().execute().data

    if f["status"] != "packed":
        raise HTTPException(409, "Fulfillment must be packed first")

    return (
        supabase.table("fulfillments")
        .update({
            "status": "shipped",
            "shipped_at": datetime.utcnow(),
            "tracking_number": tracking_number,
            "carrier": carrier,
        })
        .eq("id", fulfillment_id)
        .execute()
    ).data[0]

@router.post("/{fulfillment_id}/deliver")
async def mark_delivered(fulfillment_id: str):
    f = supabase.table("fulfillments").select("*").eq("id", fulfillment_id).single().execute().data

    if f["status"] != "shipped":
        raise HTTPException(409, "Only shipped fulfillments can be delivered")

    return (
        supabase.table("fulfillments")
        .update({
            "status": "delivered",
            "delivered_at": datetime.utcnow(),
        })
        .eq("id", fulfillment_id)
        .execute()
    ).data[0]

@router.post("/{fulfillment_id}/delay")
async def mark_delayed(
    fulfillment_id: str,
    reason: str,
):
    f = supabase.table("fulfillments").select("*").eq("id", fulfillment_id).single().execute().data

    if f["status"] not in {"pending", "packed", "shipped"}:
        raise HTTPException(409, "Cannot delay this fulfillment")

    HumanHandoffService.trigger(
        session_id=None,
        user_id=f["order_id"],
        reason="fulfillment_delay",
        summary=reason,
    )

    return (
        supabase.table("fulfillments")
        .update({
            "status": "delayed",
            "delay_reason": reason,
        })
        .eq("id", fulfillment_id)
        .execute()
    ).data[0]

@router.post("/{fulfillment_id}/fail")
async def mark_failed(
    fulfillment_id: str,
    reason: str,
):
    HumanHandoffService.trigger(
        session_id=None,
        user_id=None,
        reason="fulfillment_failed",
        summary=reason,
    )

    return (
        supabase.table("fulfillments")
        .update({
            "status": "failed",
            "failure_reason": reason,
        })
        .eq("id", fulfillment_id)
        .execute()
    ).data[0]


from langchain.tools import tool
from app.database import supabase
from app.core.redis_bus import EventBus


@tool
def schedule_fulfillment_tool(
    order_id: str,
    fulfillment_type: str = "delivery",   # 'delivery' | 'pickup' | 'reservation'
    scheduled_for: str | None = None,     # ISO datetime string
    location_note: str | None = None
) -> dict:
    """
    Schedule fulfillment for an order. Use this when user chooses delivery / pickup
    time and location.

    - fulfillment_type: 'delivery', 'pickup', or 'reservation'
    - scheduled_for: optional datetime string
    - location_note: note like "Store #23 - Pickup Counter"
    """
    # Basic existence check
    res = supabase.table("orders").select("id, user_id, status").eq("id", order_id).single().execute()
    if not res.data:
        return {"error": "Order not found"}

    fulfillment = {
        "order_id": order_id,
        "status": "scheduled",
        "fulfillment_type": fulfillment_type,
        "scheduled_for": scheduled_for,
        "location_note": location_note,
    }

    created = supabase.table("fulfillments").insert(fulfillment).execute()
    return created.data[0]


@tool
def get_fulfillment_status_tool(order_id: str) -> dict:
    """
    Check fulfillment status for a given order.
    Use when user asks 'Where is my order?' or 'Is my pickup ready?'
    """
    res = (
        supabase.table("fulfillments")
        .select("*")
        .eq("order_id", order_id)
        .order("created_at", desc=True)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return {"status": "not_scheduled"}
    return res.data

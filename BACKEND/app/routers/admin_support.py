from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.database import supabase
from app.core.redis_bus import EventBus

router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])


@router.get("/tickets")
async def get_all_tickets(
    status: str = "open",
    user_id: str = Depends(get_current_user_id),
):
    """
    Fetch queue for the support dashboard.
    support_tickets: (id, user_id, order_id, ticket_status, dispute_type,
                      issue_summary, conversation_summary, sentiment_score,
                      resolved_by, resolution_notes, failure_count,
                      created_at, updated_at, ...)
    """
    res = (
        supabase.table("support_tickets")
        .select("*, users(full_name, phone_number)")
        .eq("ticket_status", status)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


@router.get("/stats")
async def get_support_stats(user_id: str = Depends(get_current_user_id)):
    """
    Aggregate counts for dashboard charts.
    """
    open_tickets = (
        supabase.table("support_tickets")
        .select("id", count="exact")
        .eq("ticket_status", "open")
        .execute()
    )
    resolved = (
        supabase.table("support_tickets")
        .select("id", count="exact")
        .eq("ticket_status", "resolved_human")
        .execute()
    )
    return {
        "open_count": open_tickets.count,
        "resolved_count": resolved.count,
    }


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    status: str | None = None,
    resolution_notes: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    Update ticket status / resolution notes.
    If status is set, we mark resolved_by = 'human_agent' (for now).
    Also broadcasts an update event to support dashboard via Redis.
    """
    payload: dict = {}
    if status:
        payload["ticket_status"] = status
        payload["resolved_by"] = "human_agent"  # TODO: use actual agent id
    if resolution_notes is not None:
        payload["resolution_notes"] = resolution_notes

    if not payload:
        return {"status": "no_change"}

    res = (
        supabase.table("support_tickets")
        .update(payload)
        .eq("id", ticket_id)
        .execute()
    )

    ticket = res.data[0] if res.data else None

    if ticket:
        await EventBus.notify_support_dashboard("ticket_updated", ticket)

    return {"status": "updated", "ticket": ticket}

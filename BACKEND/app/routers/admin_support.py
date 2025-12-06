from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.database import supabase

router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])

@router.get("/tickets")
async def get_all_tickets(status: str = "open", user_id: str = Depends(get_current_user_id)):
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
    return {"open_count": open_tickets.count, "resolved_count": resolved.count}


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    status: str | None = None,
    resolution_notes: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    payload = {}
    if status:
        payload["ticket_status"] = status
        payload["resolved_by"] = "human_agent"  # you can inject real agent id later
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
    return {"status": "updated", "ticket": res.data[0] if res.data else None}

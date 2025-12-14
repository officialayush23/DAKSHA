from fastapi import APIRouter, Depends
from app.database import supabase
from app.core.redis_bus import EventBus
from app.core.rbac import require_role

router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])


@router.get("/tickets")
async def get_all_tickets(
    status: str = "open",
    _rbac = Depends(require_role("support_agent")),
):
    res = (
        supabase.table("support_tickets")
        .select("*, users(full_name, phone_number)")
        .eq("ticket_status", status)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


@router.get("/stats")
async def get_support_stats(
    _rbac = Depends(require_role("support_agent")),
):
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
    _rbac = Depends(require_role("support_agent")),
):
    payload = {}
    if status:
        payload["ticket_status"] = status
        payload["resolved_by"] = "human_agent"
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

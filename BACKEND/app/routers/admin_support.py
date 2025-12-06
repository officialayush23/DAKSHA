from fastapi import APIRouter, Depends
from app.auth import get_current_user_id
from app.database import supabase

router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])

@router.get("/tickets")
async def get_all_tickets(status: str = "open", user_id: str = Depends(get_current_user_id)):
    """
    Fetches queue for the support dashboard.
    """
    res = supabase.table("support_tickets")\
        .select("*, users(full_name, phone_number)")\
        .eq("ticket_status", status)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

@router.get("/stats")
async def get_support_stats(user_id: str = Depends(get_current_user_id)):
    """
    Returns data for the Analytics Charts on the Dashboard.
    """
    # Note: Complex aggregation usually better in SQL RPC, but this works for MVP
    open_tickets = supabase.table("support_tickets").select("id", count="exact").eq("ticket_status", "open").execute()
    resolved = supabase.table("support_tickets").select("id", count="exact").eq("ticket_status", "resolved_human").execute()
    
    return {
        "open_count": open_tickets.count,
        "resolved_count": resolved.count
    }
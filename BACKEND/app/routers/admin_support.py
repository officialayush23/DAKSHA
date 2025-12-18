from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase
from app.core.rbac import require_role
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None

@router.get("/stats")
async def get_support_stats(_auth = Depends(require_role("support_agent"))):
    open_count = supabase.table("support_tickets").select("id", count="exact", head=True).eq("ticket_status", "open").execute().count
    resolved_count = supabase.table("support_tickets").select("id", count="exact", head=True).eq("ticket_status", "resolved_human").execute().count
    return {"open_count": open_count, "resolved_count": resolved_count}

@router.get("/tickets")
async def list_tickets(status: str = "active", _auth = Depends(require_role("support_agent"))):
    query = supabase.table("support_tickets").select("*, users(full_name, avatar_url)")
    
    if status == "active":
        query = query.in_("ticket_status", ["open", "investigating"])
    elif status == "history":
        query = query.in_("ticket_status", ["resolved_human", "resolved_bot", "closed"])
        
    res = query.order("created_at", desc=True).limit(50).execute()
    return res.data

@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, data: TicketUpdate, _auth = Depends(require_role("support_agent"))):
    payload = {}
    if data.status: payload["ticket_status"] = data.status
    if data.resolution_notes: payload["resolution_notes"] = data.resolution_notes
    
    supabase.table("support_tickets").update(payload).eq("id", ticket_id).execute()
    return {"status": "updated"}
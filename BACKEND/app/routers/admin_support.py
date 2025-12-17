from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import supabase
from app.core.redis_bus import EventBus
from app.core.rbac import require_role

router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])


@router.get("/tickets")
async def get_all_tickets(
    status: str = "open",
    _rbac = Depends(require_role("support_agent")),
):
    try:
        query = (
            supabase.table("support_tickets")
            .select("*, users(full_name, phone_number, avatar_url)")
            .order("created_at", desc=True)
        )
        
        # --- ENUM LOGIC FIX ---
        if status == "history":
            # Fetch ALL archived/completed statuses
            query = query.in_("ticket_status", ["resolved_bot", "resolved_human", "closed"])
        elif status == "active":
             # Fetch all working statuses
            query = query.in_("ticket_status", ["open", "investigating"])
        elif status != "all":
            # Fetch exact status match (e.g., just 'open' or just 'investigating')
            query = query.eq("ticket_status", status)
            
        res = query.execute()
        return res.data
        
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/stats")
async def get_support_stats(
    _rbac = Depends(require_role("support_agent")),
):
    try:
        # We fetch a quick summary by status
        # Note: Supabase doesn't have a simple "GROUP BY" in the JS client without RPC, 
        # so we do individual counts for the most critical ones or 2 queries.
        
        # 1. Active Tickets
        open_res = supabase.table("support_tickets").select("id", count="exact", head=True).in_("ticket_status", ["open", "investigating"]).execute()
        
        # 2. Resolved (Human)
        resolved_res = supabase.table("support_tickets").select("id", count="exact", head=True).eq("ticket_status", "resolved_human").execute()
        
        return {
            "open_count": open_res.count or 0,
            "resolved_count": resolved_res.count or 0
        }
    except Exception as e:
        return {"open_count": 0, "resolved_count": 0}


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    status: str | None = None,
    resolution_notes: str | None = None,
    _rbac = Depends(require_role("support_agent")),
):
    try:
        payload = {}
        if status:
            # Validating input against your Enum
            valid_statuses = ["open", "investigating", "resolved_bot", "resolved_human", "closed"]
            if status not in valid_statuses:
                 raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")
            
            payload["ticket_status"] = status
            
            if status in ["resolved_human", "closed"]:
                payload["resolved_by"] = "human_agent"
                
        if resolution_notes:
            payload["resolution_notes"] = resolution_notes
            
        payload["updated_at"] = "now()"

        if not payload:
            return {"status": "no_change"}

        res = supabase.table("support_tickets").update(payload).eq("id", ticket_id).execute()
        return {"status": "updated", "data": res.data}

    except Exception as e:
        print(f"Update Error: {e}")
        raise HTTPException(500, detail=str(e))
    
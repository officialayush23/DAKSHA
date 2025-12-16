# from fastapi import APIRouter, Depends, HTTPException, Query
# from app.database import supabase
# from app.core.auth import get_current_user_id
# from pydantic import BaseModel
# from typing import Optional

# router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])

# # ---------------------------------------------------------
# # 🛡️ SECURITY DEPENDENCY (RBAC Check)
# # ---------------------------------------------------------
# async def verify_support_agent(user_id: str = Depends(get_current_user_id)):
#     """
#     1. Authenticates the user via JWT.
#     2. Queries 'public.user_roles' to verify 'support_agent' role.
#     """
#     try:
#         # Query the user_roles table
#         res = (
#             supabase.table("user_roles")
#             .select("role")
#             .eq("user_id", user_id)
#             .execute()
#         )
        
#         # Flatten the list of roles (e.g., ['store_manager', 'support_agent'])
#         user_roles = [record['role'] for record in (res.data or [])]
        
#         # Check if they have the required role (or super_admin)
#         if "support_agent" in user_roles or "super_admin" in user_roles:
#             return user_id
            
#         print(f"⛔ Access Denied for {user_id}. Roles found: {user_roles}")
#         raise HTTPException(403, "Access Denied: You are not a Support Agent.")

#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         print(f"⚠️ Auth Check Error: {e}")
#         raise HTTPException(401, "Authorization verification failed.")

# # --- SCHEMAS ---
# class TicketUpdate(BaseModel):
#     status: Optional[str] = None
#     resolution_notes: Optional[str] = None

# # ---------------------------------------------------------
# # 1. GET TICKETS (Protected)
# # ---------------------------------------------------------
# @router.get("/tickets")
# async def get_all_tickets(
#     status: str = "open", 
#     agent_id: str = Depends(verify_support_agent) # <--- Enforces the check
# ):
#     try:
#         query = (
#             supabase.table("support_tickets")
#             .select("*, users(full_name, phone_number, avatar_url)")
#             .order("created_at", desc=True)
#         )
        
#         if status != "all":
#             # Map frontend "resolved_human" to backend logic if needed, 
#             # or just pass through exactly what DB uses
#             query = query.eq("ticket_status", status)
            
#         res = query.execute()
#         return res.data
        
#     except Exception as e:
#         raise HTTPException(500, detail=str(e))

# # ---------------------------------------------------------
# # 2. GET STATS (Protected)
# # ---------------------------------------------------------
# @router.get("/stats")
# async def get_support_stats(agent_id: str = Depends(verify_support_agent)):
#     try:
#         # Count Open
#         open_res = supabase.table("support_tickets")\
#             .select("id", count="exact", head=True)\
#             .eq("ticket_status", "open")\
#             .execute()
            
#         # Count Resolved (Checking specifically for human resolved)
#         resolved_res = supabase.table("support_tickets")\
#             .select("id", count="exact", head=True)\
#             .eq("ticket_status", "resolved_human")\
#             .execute()
            
#         return {
#             "open_count": open_res.count or 0,
#             "resolved_count": resolved_res.count or 0
#         }
#     except Exception as e:
#         print(f"Stats Error: {e}")
#         return {"open_count": 0, "resolved_count": 0}

# # ---------------------------------------------------------
# # 3. UPDATE TICKET (Protected)
# # ---------------------------------------------------------

# @router.patch("/tickets/{ticket_id}")
# async def update_ticket(
#     ticket_id: str, 
#     status: str = Query(None), 
#     resolution_notes: str = Query(None),
#     agent_id: str = Depends(verify_support_agent)
# ):
#     try:
#         payload = {}
#         if status:
#             payload["ticket_status"] = status
#             payload["resolved_by"] = "human_agent" # Mark as human action
            
#         if resolution_notes:
#             payload["resolution_notes"] = resolution_notes
            
#         payload["updated_at"] = "now()"

#         if not payload:
#             return {"status": "no_change"}

#         # Perform Update
#         res = supabase.table("support_tickets").update(payload).eq("id", ticket_id).execute()
        
#         # Note: Your Redis EventBus logic would go here if you are using it
#         # await EventBus.notify_support_dashboard("ticket_updated", res.data[0])

#         return {"status": "updated", "data": res.data}

#     except Exception as e:
#         print(f"Patch Error: {e}")
#         # Even if 500 happens, we know from your logs DB often updates anyway.
#         # But for API correctness, we catch exceptions.
#         raise HTTPException(500, detail=str(e))
    
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import supabase
from app.core.auth import get_current_user_id
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/support", tags=["Admin: Support"])

# --- SECURITY DEPENDENCY ---
async def verify_support_agent(user_id: str = Depends(get_current_user_id)):
    try:
        res = supabase.table("user_roles").select("role").eq("user_id", user_id).execute()
        user_roles = [r['role'] for r in (res.data or [])]
        if "support_agent" in user_roles or "super_admin" in user_roles:
            return user_id
        raise HTTPException(403, "Access Denied: Support Agents Only")
    except Exception:
        raise HTTPException(403, "Authorization Failed")

# ---------------------------------------------------------
# 1. GET TICKETS
# ---------------------------------------------------------
@router.get("/tickets")
async def get_all_tickets(
    status: str = "open", 
    agent_id: str = Depends(verify_support_agent)
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

# ---------------------------------------------------------
# 2. GET STATS
# ---------------------------------------------------------
@router.get("/stats")
async def get_support_stats(agent_id: str = Depends(verify_support_agent)):
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

# ---------------------------------------------------------
# 3. UPDATE TICKET
# ---------------------------------------------------------
@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str, 
    status: str = Query(None), 
    resolution_notes: str = Query(None),
    agent_id: str = Depends(verify_support_agent)
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
    
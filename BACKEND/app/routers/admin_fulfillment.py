# src/app/routers/admin_fulfillment.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional
from app.database import supabase
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/admin/fulfillment", tags=["Admin: Fulfillment Agent"])

# --- UPDATED CONTEXT LOADER ---
async def get_agent_context(
    source_id: Optional[str] = Query(None), # Frontend passes this now
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, str]:
    try:
        # 1. Fetch ALL roles for this user
        # We need to see if ANY of their roles match the requested source_id
        res = (
            supabase.table("user_roles")
            .select("role, warehouse_id, store_id")
            .eq("user_id", user_id)
            .execute()
        )
        
        user_roles = res.data or []
        
        # 2. Super Admin Bypass
        # Check user identity separately if needed, or trust the role check below if super_admins have rows in user_roles
        
        # 3. Determine Target Location
        target_id = source_id
        
        # If frontend didn't send an ID, try to find a default one (Fallback)
        if not target_id:
            default_assignment = next((r for r in user_roles if r['store_id'] or r['warehouse_id']), None)
            if default_assignment:
                target_id = default_assignment.get('store_id') or default_assignment.get('warehouse_id')
        
        if not target_id:
             raise HTTPException(400, "No Location ID provided and no default found.")

        # 4. Verify Access to this specific Target Location
        # Does the user have a role row that contains this ID?
        has_access = any(
            (r['store_id'] == target_id or r['warehouse_id'] == target_id) 
            for r in user_roles
        )
        
        # Optional: Allow Super Admins access even without specific assignment row
        # (You would need to fetch the 'users' table here to check for super_admin flag if strict)

        if not has_access:
             # Double check if they are super_admin in 'users' table if you want strict bypass
             user_check = supabase.table("users").select("role").eq("id", user_id).single().execute()
             if user_check.data.get('role') != 'super_admin':
                 raise HTTPException(403, "Access Denied: You are not assigned to this location.")

        return {
            "user_id": user_id, 
            "location_id": target_id
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Auth Context Error: {e}")
        raise HTTPException(401, "Authorization failed.")

# --- ROUTES ---

@router.get("/queue")
async def get_fulfillment_queue(ctx: Dict = Depends(get_agent_context)):
    location_id = ctx['location_id']
    try:
        # Fetch orders for this specific location
        res = (
            supabase.table("fulfillment_sources")
            .select("order_id, orders!inner(*, order_items(*, product_variants(*, products(name))))")
            .eq("source_id", location_id)
            .in_("orders.status", ["pending", "processing"])
            .execute()
        )
        
        queue = []
        for item in res.data:
            if item.get('orders'):
                queue.append(item['orders'])
                
        return queue
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.post("/process/{order_id}")
async def process_order(
    order_id: str, 
    action: str = Query(...), 
    tracking_number: Optional[str] = Query(None),
    ctx: Dict = Depends(get_agent_context)
):
    try:
        if action == 'start_picking':
             supabase.table("orders").update({"status": "processing"}).eq("id", order_id).execute()
             return {"status": "processing"}

        elif action == 'ship':
            supabase.table("fulfillments").insert({
                "order_id": order_id,
                "status": "shipped",
                "fulfillment_type": "ship",
                "tracking_number": tracking_number,
                "shipped_at": "now()",
                "store_id": ctx['location_id'] # Log which store shipped it
            }).execute()
            
            supabase.table("orders").update({"status": "shipped"}).eq("id", order_id).execute()
            return {"status": "shipped"}
            
    except Exception as e:
        raise HTTPException(500, detail=str(e))
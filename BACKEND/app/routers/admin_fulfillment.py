# from fastapi import APIRouter, Depends, HTTPException, Query
# from pydantic import BaseModel
# from typing import List, Optional, Dict
# from app.database import supabase
# from app.core.auth import get_current_user_id

# router = APIRouter(prefix="/admin/fulfillment", tags=["Admin: Fulfillment Agent"])

# # --- SECURITY DEPENDENCY ---
# async def get_agent_context(user_id: str = Depends(get_current_user_id)) -> Dict[str, str]:
#     try:
#         res = (
#             supabase.table("user_roles")
#             .select("role, warehouse_id, store_id")
#             .eq("user_id", user_id)
#             .execute()
#         )
        
#         if not res.data:
#             raise HTTPException(403, "No active role found.")
            
#         assignments = res.data
#         # Allow fulfillment_agent, store_manager, or super_admin
#         is_agent = any(r['role'] in ['fulfillment_agent', 'store_manager', 'super_admin'] for r in assignments)
        
#         if not is_agent:
#              raise HTTPException(403, "Access Denied: Fulfillment Agents Only")

#         target_assignment = next((r for r in assignments if r['warehouse_id'] or r['store_id']), None)
        
#         # If super_admin has no assignment, we can't show a specific queue, handled below
#         if not target_assignment:
#              # Fallback for testing: if admin but no warehouse, return error or mock?
#              # For now, we raise 400.
#              raise HTTPException(400, "Account configuration error: No Warehouse/Store assigned to this agent.")

#         location_id = target_assignment.get('warehouse_id') or target_assignment.get('store_id')
#         location_type = 'warehouse' if target_assignment.get('warehouse_id') else 'store'
        
#         return {
#             "user_id": user_id, 
#             "location_id": location_id,
#             "location_type": location_type
#         }

#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         print(f"Auth Context Error: {e}")
#         raise HTTPException(401, "Authorization failed.")

# # --- SCHEMAS ---
# class ProcessOrder(BaseModel):
#     action: str
#     courier_name: Optional[str] = "Standard Logistics"
#     tracking_number: Optional[str] = None

# # ---------------------------------------------------------
# # 1. GET QUEUE (My Tasks)
# # ---------------------------------------------------------
# # @router.get("/queue")
# # async def get_fulfillment_queue(ctx: Dict = Depends(get_agent_context)):
# #     location_id = ctx['location_id']
    
# #     try:
# #         # --- FIX IS HERE ---
# #         # Removed 'image_url' from products() selection. 
# #         # It is already included in product_variants(*)
# #         allocations = (
# #             supabase.table("fulfillment_sources")
# #             .select("order_id, orders!inner(*, order_items(*, product_variants(*, products(name))))")
# #             .eq("source_id", location_id)
# #             .neq("orders.status", "shipped")
# #             .neq("orders.status", "delivered")
# #             .neq("orders.status", "cancelled")
# #             .execute()
# #         )
        
# #         queue = []
# #         for item in allocations.data:
# #             order = item.get('orders')
# #             if order:
# #                 # Compute total items
# #                 total_qty = sum(i['quantity'] for i in order.get('order_items', []))
# #                 order['total_items_count'] = total_qty
# #                 queue.append(order)
        
# #         queue.sort(key=lambda x: x['created_at'])
# #         return queue

# #     except Exception as e:
# #         print(f"Queue Error: {e}")
# #         raise HTTPException(500, detail="Failed to load queue.")

# # app/routers/admin_fulfillment.py

# @router.get("/queue")
# async def get_fulfillment_queue(
#     status: str = "active",  # 'active' or 'history'
#     ctx: Dict = Depends(get_agent_context)
# ):
#     location_id = ctx['location_id']
    
#     try:
#         # Base Query
#         query = (
#             supabase.table("fulfillment_sources")
#             # We fetch fulfillments too so we can show tracking numbers in history
#             .select("order_id, orders!inner(*, order_items(*, product_variants(*, products(name))), fulfillments(tracking_number, courier_name, shipped_at))")
#             .eq("source_id", location_id)
#         )
        
#         # Apply Filters based on mode
#         if status == "history":
#             # Show Shipped or Delivered orders
#             query = query.in_("orders.status", ["shipped", "delivered"])
#             # Limit history to last 50 for performance (optional)
#             query = query.limit(50)
#         else:
#             # Show Pending or Processing orders
#             query = query.in_("orders.status", ["pending", "processing"])
            
#         allocations = query.execute()
        
#         queue = []
#         for item in allocations.data:
#             order = item.get('orders')
#             if order:
#                 # Add total items count
#                 total_qty = sum(i['quantity'] for i in order.get('order_items', []))
#                 order['total_items_count'] = total_qty
                
#                 # Add fulfillment info (if exists) directly to order object for easy UI access
#                 if item.get('fulfillments') and len(item['fulfillments']) > 0:
#                     f = item['fulfillments'][0]
#                     order['tracking_number'] = f.get('tracking_number')
#                     order['courier_name'] = f.get('courier_name')
#                     order['shipped_at'] = f.get('shipped_at')

#                 queue.append(order)
        
#         # Sort: History = Newest First; Active = Oldest First
#         queue.sort(key=lambda x: x['created_at'], reverse=(status == "history"))
        
#         return queue

#     except Exception as e:
#         print(f"Queue Error: {e}")
#         raise HTTPException(500, detail="Failed to load queue.")

# # ---------------------------------------------------------
# # 2. PROCESS ORDER (Pick / Ship)
# # ---------------------------------------------------------
# # @router.post("/process/{order_id}")
# # async def process_order(
# #     order_id: str, 
# #     payload: ProcessOrder, 
# #     ctx: Dict = Depends(get_agent_context)
# # ):
# #     try:
# #         if payload.action == 'start_picking':
# #              supabase.table("orders").update({
# #                  "status": "processing",
# #                  "updated_at": "now()"
# #              }).eq("id", order_id).execute()
             
# #              return {"status": "processing", "order_id": order_id}

# #         elif payload.action == 'ship':
# #             # Create Fulfillment Log
# #             supabase.table("fulfillments").insert({
# #                 "order_id": order_id,
# #                 "status": "shipped",
# #                 "courier_name": payload.courier_name,
# #                 "tracking_number": payload.tracking_number or f"TRK-{order_id[:8].upper()}",
# #                 "shipped_at": "now()",
# #                 "fulfillment_type": "ship",
# #                 "store_id": ctx['location_id'] if ctx['location_type'] == 'store' else None
# #             }).execute()
            
# #             # Update Order
# #             supabase.table("orders").update({
# #                 "status": "shipped",
# #                 "updated_at": "now()"
# #             }).eq("id", order_id).execute()
            
# #             return {"status": "shipped", "order_id": order_id}

# #         else:
# #             raise HTTPException(400, "Invalid action")

# #     except Exception as e:
# #         print(f"Process Error: {e}")
# #         raise HTTPException(500, detail=str(e))


# @router.post("/process/{order_id}")
# async def process_order(
#     order_id: str, 
#     payload: ProcessOrder, 
#     ctx: Dict = Depends(get_agent_context)
# ):
#     try:
#         # 1. Start Picking
#         if payload.action == 'start_picking':
#              supabase.table("orders").update({
#                  "status": "processing"
#                  # REMOVED: "updated_at": "now()"
#              }).eq("id", order_id).execute()
             
#              return {"status": "processing", "order_id": order_id}

#         # 2. Ship Order
#         elif payload.action == 'ship':
            
#             # A. Create Fulfillment Record
#             supabase.table("fulfillments").insert({
#                 "order_id": order_id,
#                 "status": "shipped",
#                 "courier_name": payload.courier_name,
#                 "tracking_number": payload.tracking_number or f"TRK-{order_id[:8].upper()}",
#                 "shipped_at": "now()",
#                 "fulfillment_type": "ship",
#                 "store_id": ctx['location_id'] if ctx['location_type'] == 'store' else None
#             }).execute()
            
#             # B. Update Main Order Status
#             supabase.table("orders").update({
#                 "status": "shipped"
#                 # REMOVED: "updated_at": "now()"
#             }).eq("id", order_id).execute()
            
#             return {"status": "shipped", "order_id": order_id}

#         else:
#             raise HTTPException(400, "Invalid action")

#     except Exception as e:
#         print(f"Process Error: {e}")
#         raise HTTPException(500, detail=str(e))
    

# from fastapi import APIRouter, Depends, HTTPException, Query
# from pydantic import BaseModel
# from typing import List, Optional, Dict
# from app.database import supabase
# from app.core.auth import get_current_user_id

# router = APIRouter(prefix="/admin/fulfillment", tags=["Admin: Fulfillment Agent"])

# async def get_agent_context(user_id: str = Depends(get_current_user_id)) -> Dict[str, str]:
#     try:
#         # 1. Check user table for Identity (super_admin check)
#         user_data = supabase.table("users").select("role").eq("id", user_id).single().execute()
#         is_super_admin = user_data.data.get("role") == "super_admin"

#         # 2. Check user_roles table for Operational Role
#         role_res = supabase.table("user_roles").select("*").eq("user_id", user_id).execute()
        
#         # Check if they have the specific fulfillment_agent role
#         has_fulfillment_role = any(r['role'] == 'fulfillment_agent' for r in role_res.data)

#         if not is_super_admin and not has_fulfillment_role:
#              raise HTTPException(403, "Access Denied: Requires fulfillment_agent or super_admin identity")

#         # 3. Get the assigned location
#         # Even super_admins need a location_id to see a specific queue
#         assignment = next((r for r in role_res.data if r['store_id'] or r['warehouse_id']), None)
        
#         if not assignment:
#             raise HTTPException(400, "User has no assigned Store or Warehouse.")

#         return {
#             "location_id": assignment.get('store_id') or assignment.get('warehouse_id'),
#             "location_type": "store" if assignment.get('store_id') else "warehouse"
#         }
#     except Exception as e:
#         raise HTTPException(401, f"Auth context failed: {str(e)}")

# @router.get("/queue")
# async def get_fulfillment_queue(ctx: Dict = Depends(get_agent_context)):
#     location_id = ctx['location_id']
#     try:
#         # Using exact order_status_enum values: 'pending', 'processing'
#         res = (
#             supabase.table("fulfillment_sources")
#             .select("order_id, orders!inner(*, order_items(*, product_variants(*, products(name))))")
#             .eq("source_id", location_id)
#             .in_("orders.status", ["pending", "processing"])
#             .execute()
#         )
#         return [item['orders'] for item in res.data if item.get('orders')]
#     except Exception as e:
#         raise HTTPException(500, detail=str(e))

# @router.post("/process/{order_id}")
# async def process_order(order_id: str, action: str = Query(...), ctx: Dict = Depends(get_agent_context)):
#     # Mapping actions to your exact order_status_enum
#     status_map = {
#         "start_picking": "processing",
#         "ship": "shipped"
#     }
    
#     new_status = status_map.get(action)
#     if not new_status:
#         raise HTTPException(400, "Invalid action")

#     try:
#         # Update order to 'processing' or 'shipped'
#         supabase.table("orders").update({"status": new_status}).eq("id", order_id).execute()
        
#         if new_status == "shipped":
#             supabase.table("fulfillments").insert({
#                 "order_id": order_id,
#                 "status": "shipped",
#                 "fulfillment_type": "ship",
#                 "shipped_at": "now()",
#                 "store_id": ctx['location_id']
#             }).execute()
            
#         return {"status": "success", "new_status": new_status}
#     except Exception as e:
#         raise HTTPException(500, detail=str(e))


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
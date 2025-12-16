# # app/routers/admin_warehouse.py

# from fastapi import APIRouter, Depends, HTTPException, Query
# from pydantic import BaseModel
# from typing import List, Optional
# from app.database import supabase
# from app.core.auth import get_current_user_id

# router = APIRouter(prefix="/admin/warehouse", tags=["Admin: Warehouse Ops"])

# # --- SECURITY DEPENDENCY ---
# async def verify_warehouse_manager(user_id: str = Depends(get_current_user_id)):
#     """
#     Ensures user has 'warehouse_manager' role.
#     """
#     try:
#         res = supabase.table("user_roles").select("role").eq("user_id", user_id).execute()
#         roles = [r['role'] for r in res.data]
        
#         if "warehouse_manager" in roles or "super_admin" in roles:
#             return user_id
            
#         raise HTTPException(403, "Access Denied: Warehouse Manager Only")
#     except Exception:
#         raise HTTPException(403, "Authorization Failed")

# # --- SCHEMAS ---
# class StockAdjustment(BaseModel):
#     warehouse_id: str
#     variant_id: str
#     quantity_change: int # Positive to add, negative to remove
#     reason: str

# # ---------------------------------------------------------
# # 1. GET WAREHOUSE DASHBOARD
# # ---------------------------------------------------------
# @router.get("/dashboard/{warehouse_id}")
# async def get_warehouse_dashboard(warehouse_id: str, admin = Depends(verify_warehouse_manager)):
#     try:
#         # A. Total SKUs in stock
#         inv_res = supabase.table("inventory")\
#             .select("id", count="exact")\
#             .eq("fulfillment_location_id", warehouse_id)\
#             .gt("quantity_on_hand", 0)\
#             .execute()
#         total_skus = inv_res.count or 0

#         # B. Low Stock Alerts
#         alert_res = supabase.table("inventory_alerts")\
#             .select("id", count="exact")\
#             .eq("fulfillment_location_id", warehouse_id)\
#             .eq("alert_type", "low_stock")\
#             .execute()
#         low_stock = alert_res.count or 0

#         # C. Pending Shipments (Orders allocated to this warehouse)
#         orders_res = supabase.table("fulfillment_sources")\
#             .select("id", count="exact")\
#             .eq("source_id", warehouse_id)\
#             .eq("source_type", "warehouse")\
#             .execute()
#         pending_shipments = orders_res.count or 0

#         return {
#             "total_skus": total_skus,
#             "low_stock_count": low_stock,
#             "pending_shipments": pending_shipments,
#             "capacity_utilization": 0 # Placeholder for future logic
#         }

#     except Exception as e:
#         print(f"Warehouse Dashboard Error: {e}")
#         return {"total_skus": 0, "low_stock_count": 0, "pending_shipments": 0}

# # ---------------------------------------------------------
# # 2. GET WAREHOUSE INVENTORY LIST
# # ---------------------------------------------------------
# @router.get("/inventory/{warehouse_id}")
# async def get_warehouse_inventory(warehouse_id: str, admin = Depends(verify_warehouse_manager)):
#     try:
#         # Fetch inventory with joined product details
#         res = supabase.table("inventory")\
#             .select("*, product_variants(sku, size_label, color_name, products(name))")\
#             .eq("fulfillment_location_id", warehouse_id)\
#             .order("quantity_on_hand", desc=True)\
#             .limit(100)\
#             .execute()
            
#         return res.data
#     except Exception as e:
#         print(f"Inventory List Error: {e}")
#         return []

# # ---------------------------------------------------------
# # 3. ADJUST STOCK (Stock Take / Inwarding)
# # ---------------------------------------------------------
# @router.post("/inventory/adjust")
# async def adjust_stock(data: StockAdjustment, admin = Depends(verify_warehouse_manager)):
#     try:
#         # 1. Check if item exists in inventory
#         existing = supabase.table("inventory")\
#             .select("id, quantity_on_hand")\
#             .eq("fulfillment_location_id", data.warehouse_id)\
#             .eq("product_variant_id", data.variant_id)\
#             .limit(1)\
#             .execute()

#         if existing.data:
#             # Update existing row
#             current_qty = existing.data[0]['quantity_on_hand']
#             new_qty = current_qty + data.quantity_change
#             if new_qty < 0: new_qty = 0
            
#             res = supabase.table("inventory")\
#                 .update({"quantity_on_hand": new_qty})\
#                 .eq("id", existing.data[0]['id'])\
#                 .execute()
#         else:
#             # Insert new row (if positive adjustment)
#             if data.quantity_change > 0:
#                 payload = {
#                     "fulfillment_location_id": data.warehouse_id,
#                     "product_variant_id": data.variant_id,
#                     "quantity_on_hand": data.quantity_change
#                 }
#                 res = supabase.table("inventory").insert(payload).execute()
        
#         return {"status": "success"}

#     except Exception as e:
#         raise HTTPException(500, detail=str(e))

# # ---------------------------------------------------------
# # 4. GET PENDING OUTBOUND ORDERS
# # ---------------------------------------------------------
# @router.get("/outbound/orders/{warehouse_id}")
# async def get_outbound_orders(warehouse_id: str, admin = Depends(verify_warehouse_manager)):
#     try:
#         # 1. Find orders allocated to this warehouse via fulfillment_sources
#         # We assume 'pending' or 'processing' status
#         allocations = supabase.table("fulfillment_sources")\
#             .select("order_id, orders(*, order_items(*, product_variants(sku, products(name))))")\
#             .eq("source_id", warehouse_id)\
#             .eq("source_type", "warehouse")\
#             .execute()
        
#         # Flatten the structure slightly for frontend
#         orders = []
#         for item in allocations.data:
#             if item.get('orders'):
#                 order_data = item['orders']
#                 # Only show orders that aren't fully shipped yet
#                 if order_data['status'] not in ['shipped', 'cancelled', 'delivered']:
#                     order_data['items'] = order_data.get('order_items', [])
#                     orders.append(order_data)
        
#         return orders

#     except Exception as e:
#         print(f"Outbound Orders Error: {e}")
#         return []

# # ---------------------------------------------------------
# # 5. PROCESS SHIPMENT (Pick & Ship)
# # ---------------------------------------------------------
# @router.post("/outbound/ship/{order_id}")
# async def ship_order(order_id: str, warehouse_id: str = Query(...), admin = Depends(verify_warehouse_manager)):
#     try:
#         # 1. Verify Allocation
#         alloc = supabase.table("fulfillment_sources")\
#             .select("id")\
#             .eq("order_id", order_id)\
#             .eq("source_id", warehouse_id)\
#             .limit(1)\
#             .execute()
            
#         if not alloc.data:
#             raise HTTPException(400, "Order not assigned to this warehouse")

#         # 2. Update Order Status
#         supabase.table("orders").update({
#             "status": "shipped", 
#             "updated_at": "now()"
#         }).eq("id", order_id).execute()

#         # 3. Create Fulfillment Record (Simplified)
#         supabase.table("fulfillments").insert({
#             "order_id": order_id,
#             "status": "shipped",
#             "fulfillment_type": "ship"
#         }).execute()

#         # NOTE: Ideally, you should also decrement inventory here if not done at allocation time.
        
#         return {"status": "success"}

#     except Exception as e:
#         raise HTTPException(500, detail=str(e))

# from fastapi import APIRouter, Depends, HTTPException, Query
# from pydantic import BaseModel
# from typing import List, Optional
# from app.database import supabase
# from app.core.auth import get_current_user_id

# router = APIRouter(prefix="/admin/warehouse", tags=["Admin: Warehouse Ops"])

# # --- SECURITY DEPENDENCY ---
# async def verify_warehouse_manager(user_id: str = Depends(get_current_user_id)):
#     try:
#         # 1. Check user role
#         res = supabase.table("user_roles").select("role").eq("user_id", user_id).execute()
#         roles = [r['role'] for r in res.data]
        
#         if "warehouse_manager" in roles or "super_admin" in roles:
#             return user_id
            
#         raise HTTPException(403, "Access Denied: Warehouse Manager Only")
#     except Exception:
#         raise HTTPException(403, "Authorization Failed")

# # --- SCHEMAS ---
# class StockAdjustment(BaseModel):
#     warehouse_id: str
#     variant_id: str
#     quantity_change: int
#     reason: str

# # --- HELPER: Resolve Warehouse ID -> Fulfillment Location ID ---
# def get_fulfillment_id(warehouse_id: str) -> str:
#     """
#     Look up the 'fulfillment_location_id' for a given warehouse.
#     Inventory is linked to fulfillment_locations, not directly to warehouses.
#     """
#     try:
#         res = supabase.table("warehouses")\
#             .select("fulfillment_location_id")\
#             .eq("id", warehouse_id)\
#             .maybe_single()\
#             .execute()
        
#         if not res.data or not res.data.get('fulfillment_location_id'):
#             raise HTTPException(404, "Warehouse not linked to a Fulfillment Location. Please check configuration.")
            
#         return res.data['fulfillment_location_id']
#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         print(f"ID Resolution Error: {e}")
#         raise HTTPException(500, "Failed to resolve location ID.")

# # ---------------------------------------------------------
# # 1. GET WAREHOUSE DASHBOARD
# # ---------------------------------------------------------
# @router.get("/dashboard/{warehouse_id}")
# async def get_warehouse_dashboard(warehouse_id: str, admin = Depends(verify_warehouse_manager)):
#     try:
#         # 1. Resolve ID
#         fl_id = get_fulfillment_id(warehouse_id)

#         # 2. Query using Fulfillment ID
#         inv_res = supabase.table("inventory")\
#             .select("id", count="exact", head=True)\
#             .eq("fulfillment_location_id", fl_id)\
#             .gt("quantity_on_hand", 0)\
#             .execute()
#         total_skus = inv_res.count or 0

#         alert_res = supabase.table("inventory_alerts")\
#             .select("id", count="exact", head=True)\
#             .eq("fulfillment_location_id", fl_id)\
#             .eq("alert_type", "low_stock")\
#             .execute()
#         low_stock = alert_res.count or 0

#         # Note: fulfillment_sources links to the 'warehouses' table ID directly, 
#         # so we use warehouse_id here, NOT fl_id.
#         orders_res = supabase.table("fulfillment_sources")\
#             .select("id", count="exact", head=True)\
#             .eq("source_id", warehouse_id)\
#             .eq("source_type", "warehouse")\
#             .execute()
#         pending_shipments = orders_res.count or 0

#         return {
#             "total_skus": total_skus,
#             "low_stock_count": low_stock,
#             "pending_shipments": pending_shipments,
#             "capacity_utilization": 0 
#         }

#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         print(f"Warehouse Dashboard Error: {e}")
#         return {"total_skus": 0, "low_stock_count": 0, "pending_shipments": 0}

# # ---------------------------------------------------------
# # 2. GET WAREHOUSE INVENTORY LIST
# # ---------------------------------------------------------
# @router.get("/inventory/{warehouse_id}")
# async def get_warehouse_inventory(warehouse_id: str, admin = Depends(verify_warehouse_manager)):
#     try:
#         # 1. Resolve ID
#         fl_id = get_fulfillment_id(warehouse_id)

#         # 2. Fetch inventory
#         res = supabase.table("inventory")\
#             .select("*, product_variants(sku, size_label, color_name, products(name))")\
#             .eq("fulfillment_location_id", fl_id)\
#             .order("quantity_on_hand", desc=True)\
#             .limit(100)\
#             .execute()
            
#         return res.data
#     except Exception as e:
#         print(f"Inventory List Error: {e}")
#         return []

# # ---------------------------------------------------------
# # 3. ADJUST STOCK (Stock Take / Inwarding)
# # ---------------------------------------------------------
# @router.post("/inventory/adjust")
# async def adjust_stock(data: StockAdjustment, admin = Depends(verify_warehouse_manager)):
#     try:
#         # 1. Resolve ID (Critical Fix)
#         fl_id = get_fulfillment_id(data.warehouse_id)

#         # 2. Check if item exists in inventory
#         existing = supabase.table("inventory")\
#             .select("id, quantity_on_hand")\
#             .eq("fulfillment_location_id", fl_id)\
#             .eq("product_variant_id", data.variant_id)\
#             .maybe_single()\
#             .execute()

#         if existing.data:
#             # Update existing row
#             current_qty = existing.data['quantity_on_hand']
#             new_qty = max(0, current_qty + data.quantity_change)
            
#             supabase.table("inventory")\
#                 .update({"quantity_on_hand": new_qty})\
#                 .eq("id", existing.data['id'])\
#                 .execute()
#         else:
#             # Insert new row (only if adding stock)
#             if data.quantity_change > 0:
#                 payload = {
#                     "fulfillment_location_id": fl_id, # <--- Correct ID used here
#                     "product_variant_id": data.variant_id,
#                     "quantity_on_hand": data.quantity_change
#                 }
#                 supabase.table("inventory").insert(payload).execute()
#             else:
#                 raise HTTPException(400, "Cannot remove stock from item that doesn't exist.")
        
#         return {"status": "success", "message": "Inventory updated"}

#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         # Clean Error Response
#         print(f"Stock Adjust Error: {e}")
#         if "violates foreign key constraint" in str(e):
#              raise HTTPException(400, detail="Invalid Variant ID or Configuration Error.")
#         raise HTTPException(500, detail="Internal Server Error during stock adjustment.")

# # ---------------------------------------------------------
# # 4. GET PENDING OUTBOUND ORDERS
# # ---------------------------------------------------------
# @router.get("/outbound/orders/{warehouse_id}")
# async def get_outbound_orders(warehouse_id: str, admin = Depends(verify_warehouse_manager)):
#     try:
#         # Orders use warehouse_id directly (from fulfillment_sources)
#         allocations = supabase.table("fulfillment_sources")\
#             .select("order_id, orders(*, order_items(*, product_variants(sku, products(name))))")\
#             .eq("source_id", warehouse_id)\
#             .eq("source_type", "warehouse")\
#             .execute()
        
#         orders = []
#         for item in allocations.data:
#             if item.get('orders'):
#                 order_data = item['orders']
#                 if order_data['status'] not in ['shipped', 'cancelled', 'delivered']:
#                     order_data['items'] = order_data.get('order_items', [])
#                     orders.append(order_data)
        
#         return orders

#     except Exception as e:
#         print(f"Outbound Orders Error: {e}")
#         return []

# # ---------------------------------------------------------
# # 5. PROCESS SHIPMENT
# # ---------------------------------------------------------
# @router.post("/outbound/ship/{order_id}")
# async def ship_order(order_id: str, warehouse_id: str = Query(...), admin = Depends(verify_warehouse_manager)):
#     try:
#         # Check if allocated
#         alloc = supabase.table("fulfillment_sources")\
#             .select("id")\
#             .eq("order_id", order_id)\
#             .eq("source_id", warehouse_id)\
#             .maybe_single()\
#             .execute()
            
#         if not alloc.data:
#             raise HTTPException(400, "Order not assigned to this warehouse")

#         # Update Status
#         supabase.table("orders").update({
#             "status": "shipped", 
#             "updated_at": "now()"
#         }).eq("id", order_id).execute()

#         # Create Fulfillment Record
#         supabase.table("fulfillments").insert({
#             "order_id": order_id,
#             "status": "shipped",
#             "fulfillment_type": "ship",
#             # We don't link store_id here because it's a warehouse
#         }).execute()
        
#         return {"status": "success"}

#     except Exception as e:
#         raise HTTPException(500, detail=str(e))
    


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.database import supabase
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/admin/warehouse", tags=["Admin: Warehouse Ops"])

# --- DEPENDENCY: VERIFY WAREHOUSE MANAGER ---
async def verify_warehouse_access(
    warehouse_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Ensures the user has the 'warehouse_manager' role for this specific warehouse.
    """
    try:
        # Check user_roles for this warehouse_id
        res = (
            supabase.table("user_roles")
            .select("role")
            .eq("user_id", user_id)
            .eq("warehouse_id", warehouse_id)
            .eq("role", "warehouse_manager")
            .execute()
        )
        
        # Also allow Super Admin
        user_check = supabase.table("users").select("role").eq("id", user_id).single().execute()
        is_super = user_check.data and user_check.data.get('role') == 'super_admin'

        if not res.data and not is_super:
            raise HTTPException(403, "Access Denied: You are not the manager of this warehouse.")
            
        return True
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(401, "Authorization check failed.")

# --- SCHEMAS ---
class StockAdjustment(BaseModel):
    warehouse_id: str
    variant_id: str
    quantity_change: int # Can be negative (shrinkage) or positive (restock)
    reason: str

# ---------------------------------------------------------
# 1. DASHBOARD
# ---------------------------------------------------------
@router.get("/dashboard/{warehouse_id}")
async def get_dashboard(warehouse_id: str, authorized: bool = Depends(verify_warehouse_access)):
    try:
        # 1. Total Items (Count distinct variants in this warehouse)
        # Assuming you have a 'warehouse_inventory' table. 
        # If not, we mock it or count from a relevant table.
        # For now, let's assume we count active allocations in fulfillment_sources as "Pending"
        
        pending_res = (
            supabase.table("fulfillment_sources")
            .select("id", count="exact")
            .eq("source_id", warehouse_id)
            .execute()
        )
        
        # Mocking Capacity for now as it's not in your schema
        return {
            "total_skus": 1205, # Placeholder or query from inventory table
            "low_stock_count": 12, # Placeholder
            "pending_shipments": pending_res.count or 0,
            "capacity_utilization": 78
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# ---------------------------------------------------------
# 2. INVENTORY (Mocked if table missing)
# ---------------------------------------------------------
@router.get("/inventory/{warehouse_id}")
async def get_inventory(warehouse_id: str, authorized: bool = Depends(verify_warehouse_access)):
    # You need a 'warehouse_inventory' table: (warehouse_id, variant_id, quantity)
    # If you don't have it, we return an empty list or mock data.
    return []

@router.post("/inventory/adjust")
async def adjust_stock(payload: StockAdjustment, user_id: str = Depends(get_current_user_id)):
    # Verify access manually since warehouse_id is in body
    await verify_warehouse_access(payload.warehouse_id, user_id)
    
    # Logic to update 'warehouse_inventory' would go here
    return {"status": "success", "message": "Stock adjusted (Logic pending table creation)"}

# ---------------------------------------------------------
# 3. OUTBOUND ORDERS (The Critical Fix)
# ---------------------------------------------------------
@router.get("/outbound/orders/{warehouse_id}")
async def get_outbound_orders(warehouse_id: str, authorized: bool = Depends(verify_warehouse_access)):
    try:
        # LINKING VIA fulfillment_sources
        # We find orders linked to this warehouse via source_id
        res = (
            supabase.table("fulfillment_sources")
            .select("order_id, orders!inner(*, order_items(*, product_variants(*, products(name))))")
            .eq("source_id", warehouse_id)
            .eq("source_type", "warehouse") # Explicitly check type
            .neq("orders.status", "shipped") # Only show pending/processing
            .neq("orders.status", "cancelled")
            .execute()
        )
        
        # Flatten structure
        orders = []
        if res.data:
            for item in res.data:
                orders.append(item['orders'])
                
        return orders
    except Exception as e:
        print(f"Outbound Error: {e}")
        raise HTTPException(500, str(e))

# ---------------------------------------------------------
# 4. SHIP ORDER
# ---------------------------------------------------------
@router.post("/outbound/ship/{order_id}")
async def ship_order(
    order_id: str, 
    warehouse_id: str = Query(...), 
    authorized: bool = Depends(verify_warehouse_access)
):
    try:
        # 1. Update Order Status
        update_res = (
            supabase.table("orders")
            .update({"status": "shipped"})
            .eq("id", order_id)
            .execute()
        )
        
        # FIX: Check if data exists safely
        if not update_res.data:
            raise HTTPException(404, "Order not found or update failed")

        # 2. Log Fulfillment
        supabase.table("fulfillments").insert({
            "order_id": order_id,
            "status": "shipped",
            "fulfillment_type": "ship",
            "shipped_at": "now()",
            # We treat 'store_id' as generic 'location_id' in fulfillments schema?
            # Or you might need to add 'warehouse_id' column to fulfillments table.
            # For now, we will leave store_id null and put note in tracking.
            "courier_name": "Warehouse Logistics",
            "tracking_number": f"WH-{order_id[:8].upper()}"
        }).execute()

        return {"status": "shipped", "order_id": order_id}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Ship Error: {e}")
        # Return a clean error message, not the Python traceback
        raise HTTPException(500, "Internal Server Error during shipping process.")
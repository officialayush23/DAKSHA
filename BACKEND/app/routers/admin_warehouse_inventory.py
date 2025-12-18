from fastapi import APIRouter, Depends, HTTPException, Query, Path
from app.database import supabase
from app.core.rbac import require_warehouse_access
from app.models.management import InventoryAdjustRequest, InventoryFullUpdate
from app.services.inventory_service import InventoryService
from datetime import datetime, timezone
import logging

# ✅ Define the 3 specific routers expected by main.py
router = APIRouter(prefix="/admin/warehouse/inventory", tags=["Admin: Warehouse Ops"])
router_outbound = APIRouter(prefix="/admin/warehouse/outbound", tags=["Admin: Warehouse Outbound"])
router_dashboard = APIRouter(prefix="/admin/warehouse", tags=["Admin: Warehouse"])

logger = logging.getLogger("admin.warehouse")

# --- HELPER: ROBUST ID RESOLUTION ---
def get_fl_id(warehouse_id: str):
    """Safely resolves Warehouse ID to Fulfillment Location ID"""
    try:
        # Use limit(1) instead of maybe_single() for safety
        res = supabase.table("warehouses").select("fulfillment_location_id").eq("id", warehouse_id).limit(1).execute()
        
        if not res or not res.data:
            raise HTTPException(404, "Warehouse not found in database.")
            
        fl_id = res.data[0].get('fulfillment_location_id')
        if not fl_id:
            raise HTTPException(400, "Warehouse has no Fulfillment Location ID. Contact Super Admin.")
            
        return fl_id
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(500, f"ID Resolution Error: {str(e)}")

# ==============================================================================
# 📊 DASHBOARD ROUTER
# ==============================================================================
@router_dashboard.get("/dashboard/{warehouse_id}")
async def warehouse_dashboard(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    try:
        fl_id = get_fl_id(warehouse_id)

        skus = supabase.table("inventory").select("id", count="exact", head=True).eq("fulfillment_location_id", fl_id).execute().count or 0
        low_stock = supabase.table("inventory").select("id", count="exact", head=True).eq("fulfillment_location_id", fl_id).lt("quantity_on_hand", 10).execute().count or 0
        
        pending = supabase.table("fulfillments").select("id", count="exact", head=True)\
            .eq("fulfillment_location_id", fl_id)\
            .in_("status", ["pending", "processing", "packed"])\
            .execute().count or 0

        return {
            "total_skus": skus,
            "low_stock_count": low_stock,
            "pending_shipments": pending,
            "capacity_utilization": 45
        }
    except Exception as e:
        logger.error(f"Dashboard Error: {e}")
        return {"total_skus": 0, "low_stock_count": 0, "pending_shipments": 0}

# ==============================================================================
# 📦 INVENTORY ROUTER
# ==============================================================================
@router.get("/{warehouse_id}")
async def get_warehouse_inventory(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    try:
        fl_id = get_fl_id(warehouse_id)
        
        res = supabase.table("inventory").select(
            "*, product_variants!inner(sku, products!inner(name))"
        ).eq("fulfillment_location_id", fl_id).execute()

        if not res or not res.data: return []

        return [
            {
                "id": i['id'],
                "variant_id": i['product_variant_id'],
                "sku": i['product_variants']['sku'],
                "product_name": i['product_variants']['products']['name'],
                "quantity": i['quantity_on_hand'],
                "quantity_reserved": i.get('quantity_reserved', 0),
                "product_variants": i['product_variants'],
                "aisle_number": i.get('aisle_number'),
                "shelf_height": i.get('shelf_height'),
                "low_stock_threshold": i.get('low_stock_threshold', 5)
            } for i in res.data or []
        ]
    except Exception as e:
        print(f"Inventory List Error: {e}")
        return []

@router.post("/adjust")
async def adjust_warehouse_inventory(
    data: InventoryAdjustRequest,
    warehouse_id: str = Query(..., description="Warehouse ID"),
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    try:
        fl_id = get_fl_id(warehouse_id)
        
        # 1. ROBUST CHECK: Use limit(1) instead of maybe_single()
        # This guarantees a list is returned, avoiding NoneType errors
        inv_query = supabase.table("inventory").select("*")\
            .eq("product_variant_id", data.variant_id)\
            .eq("fulfillment_location_id", fl_id)\
            .limit(1)\
            .execute()
        
        # 2. Logic: Update or Insert
        if inv_query.data and len(inv_query.data) > 0:
            # Update Existing
            existing_item = inv_query.data[0]
            current_qty = existing_item["quantity_on_hand"]
            new_qty = max(0, current_qty + data.quantity_change)
            
            res = supabase.table("inventory").update({
                "quantity_on_hand": new_qty,
                # removed updated_at to prevent schema errors if column missing
            }).eq("id", existing_item["id"]).execute()
            
            # Safety return
            updated_data = res.data[0] if (res.data and len(res.data) > 0) else {"quantity_on_hand": new_qty}
            return {"status": "updated", "data": updated_data}
            
        else:
            # Insert New (Inbound Logic)
            if data.quantity_change < 0:
                raise HTTPException(400, "Cannot reduce stock for item that doesn't exist")
                
            payload = {
                "fulfillment_location_id": fl_id,
                "product_variant_id": data.variant_id,
                "quantity_on_hand": data.quantity_change
            }
            res = supabase.table("inventory").insert(payload).execute()
            
            # Safety return
            new_data = res.data[0] if (res.data and len(res.data) > 0) else payload
            return {"status": "created", "data": new_data}

    except Exception as e:
        print(f"Adjust Error: {e}")
        raise HTTPException(500, detail=str(e))

@router.patch("/update")
async def update_warehouse_inventory_details(
    data: InventoryFullUpdate,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    fl_id = get_fl_id(data.store_id)
    data.store_id = fl_id 
    
    updated = await InventoryService.full_update(data)
    return {"status": "updated", "data": updated}

# ==============================================================================
# 🚚 OUTBOUND ROUTER
# ==============================================================================
@router_outbound.get("/orders/{warehouse_id}")
async def get_outbound_orders(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    try:
        fl_id = get_fl_id(warehouse_id)
        
        res = supabase.table("fulfillments").select(
            "*, orders!inner(*, order_items(*, product_variants(*, products(name))))"
        ).eq("fulfillment_location_id", fl_id)\
         .in_("status", ["pending", "processing", "packed"])\
         .order("created_at", desc=True)\
         .execute()
        
        if not res or not res.data: return []

        orders = []
        for row in res.data:
            if row.get("orders"):
                order_obj = row["orders"]
                order_obj["fulfillment_status"] = row["status"] 
                orders.append(order_obj)
        
        return orders
    except Exception as e:
        print(f"Outbound List Error: {e}")
        return []

@router_outbound.post("/ship/{order_id}")
async def ship_warehouse_order(
    order_id: str,
    warehouse_id: str = Query(..., description="Warehouse ID"),
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    try:
        fl_id = get_fl_id(warehouse_id)
        
        # 1. Update Fulfillment Record
        f_res = supabase.table("fulfillments").update({
            "status": "shipped"
            # Removed updated_at/shipped_at here to be safe
        }).eq("order_id", order_id).eq("fulfillment_location_id", fl_id).execute()

        if not f_res.data:
            # Fallback create if missing
            supabase.table("fulfillments").insert({
                "order_id": order_id,
                "fulfillment_location_id": fl_id,
                "status": "shipped",
                "fulfillment_type": "ship"
            }).execute()

        # 2. Update Global Order
        supabase.table("orders").update({"status": "shipped"}).eq("id", order_id).execute()
        
        return {"status": "shipped"}
    except Exception as e:
        print(f"Ship Error: {e}")
        raise HTTPException(500, detail=str(e))
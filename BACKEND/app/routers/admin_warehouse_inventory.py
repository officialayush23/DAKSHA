# app/routers/admin_warehouse_inventory.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from app.core.database import supabase
from app.core.rbac import require_warehouse_access
from app.schemas.schemas import InventoryAdjustRequest, InventoryFullUpdate
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
        
        # Use RPC for inventory adjustment
        from app.core.rpc import RPCService
        
        reason = data.reason or f"Inventory adjustment by warehouse manager"
        RPCService.adjust_inventory(
            variant_id=data.variant_id,
            location_id=fl_id,
            delta=data.quantity_change,
            reason=reason,
        )
        
        # Read back updated inventory
        updated = (
            supabase.table("inventory")
            .select("*")
            .eq("product_variant_id", data.variant_id)
            .eq("fulfillment_location_id", fl_id)
            .maybe_single()
            .execute()
        ).data
        
        if updated:
            return {"status": "updated", "data": updated}
        else:
            # If doesn't exist and delta is positive, RPC should have created it
            # Re-read to confirm
            updated = (
                supabase.table("inventory")
                .select("*")
                .eq("product_variant_id", data.variant_id)
                .eq("fulfillment_location_id", fl_id)
                .maybe_single()
                .execute()
            ).data
            return {"status": "created", "data": updated or {"quantity_on_hand": data.quantity_change}}

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
        
        # Use RPCs for order state transition
        from app.core.rpc import RPCService
        
        # 1. Transition order state to shipped
        RPCService.transition_order_state(
            order_id=order_id,
            from_state="processing",
            to_state="shipped",
        )
        
        # 2. Ensure fulfillment exists (create if missing)
        fulfillment = (
            supabase.table("fulfillments")
            .select("id")
            .eq("order_id", order_id)
            .maybe_single()
            .execute()
        ).data
        
        if not fulfillment:
            RPCService.create_fulfillment_for_order(order_id)
        
        return {"status": "shipped"}
    except Exception as e:
        print(f"Ship Error: {e}")
        raise HTTPException(500, detail=str(e))
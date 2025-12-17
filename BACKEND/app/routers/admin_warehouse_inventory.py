# app/routers/admin_warehouse_inventory.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.rbac import require_warehouse_access
from app.models.management import InventoryFullUpdate
from app.services.inventory_service import InventoryService
from app.database import supabase
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/warehouse/inventory", tags=["Admin: Warehouse Ops"])
router_outbound = APIRouter(prefix="/admin/warehouse/outbound", tags=["Admin: Warehouse Outbound"])
router_dashboard = APIRouter(prefix="/admin/warehouse", tags=["Admin: Warehouse"])


class InventoryAdjustRequest(BaseModel):
    variant_id: str
    quantity_change: int  # positive for add, negative for subtract
    reason: Optional[str] = None


@router_dashboard.get("/dashboard/{warehouse_id}")
async def warehouse_dashboard_alias(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    """Alias for /admin/warehouse/inventory/dashboard/{warehouse_id}"""
    return InventoryService.get_fulfillment_dashboard(warehouse_id)


@router.get("/dashboard/{warehouse_id}")
async def warehouse_dashboard(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    return InventoryService.get_fulfillment_dashboard(warehouse_id)


@router.get("/{warehouse_id}")
async def get_warehouse_inventory(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    """Get all inventory items for a warehouse"""
    return InventoryService.get_store_dashboard(warehouse_id)


@router.post("/adjust")
async def adjust_warehouse_inventory(
    data: InventoryAdjustRequest,
    warehouse_id: str = Query(..., description="Warehouse ID"),
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    """Adjust inventory quantity (add or subtract)"""
    # Get current inventory
    inv = (
        supabase.table("inventory")
        .select("*")
        .eq("product_variant_id", data.variant_id)
        .eq("fulfillment_location_id", warehouse_id)
        .maybe_single()
        .execute()
    ).data
    
    if not inv:
        raise HTTPException(404, "Inventory item not found")
    
    new_qty = max(0, inv["quantity_on_hand"] + data.quantity_change)
    
    updated = (
        supabase.table("inventory")
        .update({"quantity_on_hand": new_qty})
        .eq("id", inv["id"])
        .execute()
    ).data[0]
    
    return {"status": "adjusted", "data": updated}


@router.patch("/update")
async def update_warehouse_inventory(
    data: InventoryFullUpdate,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    updated = await InventoryService.full_update(data)
    return {"status": "updated", "data": updated}


@router_outbound.get("/orders/{warehouse_id}")
async def get_outbound_orders(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    """Get pending outbound orders for a warehouse"""
    orders = (
        supabase.table("orders")
        .select(
            "*, order_items(*, product_variants(*, products(name)))"
        )
        .eq("fulfillment_location_id", warehouse_id)
        .in_("status", ["pending", "confirmed", "processing"])
        .order("created_at", desc=True)
        .execute()
    ).data or []
    
    return orders


@router_outbound.post("/ship/{order_id}")
async def ship_order(
    order_id: str,
    warehouse_id: str = Query(..., description="Warehouse ID"),
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    """Mark an order as shipped"""
    order = (
        supabase.table("orders")
        .select("*")
        .eq("id", order_id)
        .eq("fulfillment_location_id", warehouse_id)
        .maybe_single()
        .execute()
    ).data
    
    if not order:
        raise HTTPException(404, "Order not found")
    
    updated = (
        supabase.table("orders")
        .update({"status": "shipped"})
        .eq("id", order_id)
        .execute()
    ).data[0]
    
    return {"status": "shipped", "order": updated}

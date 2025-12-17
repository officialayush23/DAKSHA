# app/routers/admin_warehouse_inventory.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.rbac import require_warehouse_access
from app.models.management import InventoryFullUpdate
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/admin/warehouse/inventory", tags=["Admin: Warehouse Ops"])


@router.get("/dashboard/{warehouse_id}")
async def warehouse_dashboard(
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    return InventoryService.get_fulfillment_dashboard(warehouse_id)


@router.patch("/update")
async def update_warehouse_inventory(
    data: InventoryFullUpdate,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    updated = await InventoryService.full_update(data)
    return {"status": "updated", "data": updated}

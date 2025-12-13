from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.core.rbac import require_warehouse_access
from app.models.management import InventoryFullUpdate
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/admin/warehouse/inventory", tags=["Admin: Warehouse Ops"])


@router.get("/dashboard/{warehouse_id}")
async def warehouse_dashboard(
    warehouse_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Initial warehouse dashboard load.
    """
    return InventoryService.get_fulfillment_dashboard(warehouse_id)


@router.patch("/update")
async def update_warehouse_inventory(
    data: InventoryFullUpdate,
    _role=Depends(require_warehouse_access("store_id")),  # store_id == fulfillment_location_id
):
    """
    Warehouse stock correction / movement.
    """
    updated = await InventoryService.full_update(data)
    return {"status": "updated", "data": updated}

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.management import StoreCreate, InventoryFullUpdate
from app.database import supabase
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/admin/inventory", tags=["Admin: Store Ops"])


@router.post("/stores")
async def create_store(
    data: StoreCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Register a new store (code, name, type, location).
    """
    res = supabase.table("stores").insert(data.dict()).execute()
    return res.data[0]


@router.get("/dashboard/{store_id}")
async def get_store_dashboard(
    store_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Initial load for Store Manager dashboard.
    """
    return InventoryService.get_store_dashboard(store_id)


@router.patch("/update")
async def update_inventory_details(
    data: InventoryFullUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """
    The 'God Mode' inventory update:
    - Quantity corrections
    - Aisle / bay / shelf / display changes
    - Real-time broadcast to dashboards & kiosks
    """
    updated_item = await InventoryService.full_update(data)
    return {"status": "updated", "data": updated_item}

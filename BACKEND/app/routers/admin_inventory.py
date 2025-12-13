# app/routers/admin_inventory.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.management import StoreCreate, InventoryFullUpdate
from app.database import supabase
from app.services.inventory_service import InventoryService
from app.core.rbac import require_store_access

router = APIRouter(prefix="/admin/inventory", tags=["Admin: Store Ops"])


# ---------------------------------------------------------
# CREATE STORE / WAREHOUSE (fulfillment location)
# ---------------------------------------------------------
@router.post("/stores")
async def create_store(
    data: StoreCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Creates a store + its fulfillment_location entry.
    """

    # 1) Create fulfillment_location
    loc = (
        supabase.table("fulfillment_locations")
        .insert(
            {
                "type": data.type,  # store | warehouse | dark_store
                "name": data.name,
                "city": data.city,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "address_line": data.address_line_1,
            }
        ).execute()
    ).data[0]

    # 2) Create store
    store = (
        supabase.table("stores")
        .insert(
            {
                "store_code": data.store_code,
                "name": data.name,
                "type": data.type,
                "city": data.city,
                "address_line_1": data.address_line_1,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "fulfillment_location_id": loc["id"],
            }
        )
        .execute()
    ).data[0]

    return {"store": store, "fulfillment_location": loc}


# ---------------------------------------------------------
# DASHBOARD INITIAL LOAD
# ---------------------------------------------------------
@router.get("/dashboard/{store_id}")
async def get_store_dashboard(store_id: str, user_id: str = Depends(get_current_user_id)):
    return InventoryService.get_store_dashboard(store_id)


# ---------------------------------------------------------
# FULL INVENTORY UPDATE
# ---------------------------------------------------------
@router.patch("/update")
async def update_inventory_details(
    data: InventoryFullUpdate,
    rbac = Depends(require_store_access("store_id")),
):
    updated = await InventoryService.full_update(data)
    return {"status": "updated", "data": updated}

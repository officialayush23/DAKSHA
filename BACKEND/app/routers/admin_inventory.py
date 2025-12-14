from fastapi import APIRouter, Depends
from app.models.management import StoreCreate, InventoryFullUpdate
from app.database import supabase
from app.services.inventory_service import InventoryService
from app.core.rbac import require_role, require_store_access

router = APIRouter(prefix="/admin/inventory", tags=["Admin: Store Ops"])


# ---------------------------------------------------------
# CREATE STORE / WAREHOUSE (SUPER ADMIN ONLY)
# ---------------------------------------------------------
@router.post("/stores")
async def create_store(
    data: StoreCreate,
    _rbac = Depends(require_role("super_admin")),
):
    loc = (
        supabase.table("fulfillment_locations")
        .insert(
            {
                "type": data.type,
                "name": data.name,
                "city": data.city,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "address_line": data.address_line_1,
            }
        )
        .execute()
    ).data[0]

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
# DASHBOARD
# ---------------------------------------------------------
@router.get("/dashboard/{store_id}")
async def get_store_dashboard(
    store_id: str,
    _rbac = Depends(require_store_access("store_id")),
):
    return InventoryService.get_store_dashboard(store_id)


# ---------------------------------------------------------
# INVENTORY UPDATE
# ---------------------------------------------------------
@router.patch("/update")
async def update_inventory_details(
    data: InventoryFullUpdate,
    _rbac = Depends(require_store_access("store_id")),
):
    updated = await InventoryService.full_update(data)
    return {"status": "updated", "data": updated}

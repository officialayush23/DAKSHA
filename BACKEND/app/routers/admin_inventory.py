from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id

from app.schemas import StoreCreate, InventoryFullUpdate
from app.database import supabase, redis_client
import json

router = APIRouter(prefix="/admin/inventory", tags=["Admin: Store Ops"])

@router.post("/stores")
async def create_store(data: StoreCreate, user_id: str = Depends(get_current_user_id)):
    res = supabase.table("stores").insert(data.dict()).execute()
    return res.data[0]

@router.get("/dashboard/{store_id}")
async def get_store_dashboard(store_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Initial load for the Store Manager's Tablet.
    Returns all inventory for this specific store.
    """
    res = supabase.table("inventory")\
        .select("*, product_variants(sku, color_name, size_label, products(name))")\
        .eq("store_id", store_id)\
        .execute()
    return res.data

@router.patch("/update")
async def update_inventory_details(
    data: InventoryFullUpdate, 
    user_id: str = Depends(get_current_user_id)
):
    """
    The 'God Mode' update for inventory.
    Updates Count, Location (Aisle/Shelf), and notifies Kiosks.
    """
    # 1. Get Current Version (Optimistic Lock)
    current = supabase.table("inventory").select("version")\
        .eq("store_id", data.store_id)\
        .eq("product_variant_id", data.variant_id)\
        .single().execute()
        
    if not current.data:
        raise HTTPException(404, "Item not found in this store")

    # 2. Prepare Update Payload (Remove None values)
    update_payload = {k: v for k, v in data.dict().items() if v is not None}
    
    # Remove keys that are for identification, not update
    del update_payload['variant_id']
    del update_payload['store_id']
    
    # Increment version
    update_payload['version'] = current.data['version'] + 1

    # 3. Execute Update
    res = supabase.table("inventory").update(update_payload)\
        .eq("store_id", data.store_id)\
        .eq("product_variant_id", data.variant_id)\
        .eq("version", current.data['version'])\
        .execute()

    if not res.data:
        raise HTTPException(409, "Inventory modified by someone else. Retry.")

    # 4. ⚡ REAL-TIME BROADCAST
    # This pushes the new location/count to the Store Dashboard & Kiosks
    updated_item = res.data[0]
    await redis_client.publish(
        f"store:{data.store_id}:inventory", 
        json.dumps({
            "event": "full_update", 
            "data": updated_item
        })
    )

    return {"status": "updated", "data": updated_item}
# src/app/routers/admin_inventory_onboarding.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.rbac import require_store_access, require_warehouse_access
from app.database import supabase

router = APIRouter(
    prefix="/admin/inventory/onboard",
    tags=["Admin: Inventory Onboarding"],
)

@router.post("/store")
async def onboard_variant_to_store(
    variant_id: str,
    store_id: str,
    _rbac = Depends(require_store_access("store_id")),
):
    return _onboard(variant_id, store_id)

@router.post("/warehouse")
async def onboard_variant_to_warehouse(
    variant_id: str,
    warehouse_id: str,
    _rbac = Depends(require_warehouse_access("warehouse_id")),
):
    return _onboard(variant_id, warehouse_id)


def _onboard(variant_id: str, fulfillment_location_id: str):
    # 1. Validate variant + product
    pv = (
        supabase.table("product_variants")
        .select("id, products(is_active)")
        .eq("id", variant_id)
        .single()
        .execute()
    ).data

    if not pv:
        raise HTTPException(404, "Variant not found")

    if not pv["products"]["is_active"]:
        raise HTTPException(400, "Inactive product cannot be stocked")

    # 2. Prevent duplicates
    exists = (
        supabase.table("inventory")
        .select("id")
        .eq("product_variant_id", variant_id)
        .eq("fulfillment_location_id", fulfillment_location_id)
        .maybe_single()
        .execute()
    ).data

    if exists:
        raise HTTPException(409, "Variant already onboarded")

    # 3. Create inventory row
    inv = (
        supabase.table("inventory")
        .insert({
            "product_variant_id": variant_id,
            "fulfillment_location_id": fulfillment_location_id,
            "quantity_on_hand": 0,
        })
        .execute()
    ).data[0]

    return {"status": "onboarded", "inventory": inv}

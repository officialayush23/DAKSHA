# app/routers/inventory.py

from fastapi import APIRouter, Query
from app.database import supabase
from app.services.store_service import StoreService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ---------------------------------------------------------
# CHECK STOCK BY SKU + LOCATION
# ---------------------------------------------------------
@router.get("/check")
async def check_stock(
    sku: str,
    fulfillment_location_id: str,
):
    variant = (
        supabase.table("product_variants")
        .select("id, sku, products(name)")
        .eq("sku", sku)
        .single()
        .execute()
    ).data

    if not variant:
        return {"available": False}

    inv = (
        supabase.table("inventory")
        .select("*")
        .eq("product_variant_id", variant["id"])
        .eq("fulfillment_location_id", fulfillment_location_id)
        .maybe_single()
        .execute()
    ).data

    if not inv or inv["quantity_on_hand"] <= 0:
        return {
            "available": False,
            "sku": sku,
            "location_id": fulfillment_location_id,
        }

    return {
        "available": True,
        "sku": sku,
        "product_name": variant["products"]["name"],
        "qty": inv["quantity_on_hand"],
        "location": {
            "aisle": inv["aisle_number"],
            "bay": inv["bay_number"],
            "shelf": inv["shelf_height"],
            "display": inv["display_location"],
        },
    }


# ---------------------------------------------------------
# NEAREST STORES WITH STOCK (CHATBOT USE)
# ---------------------------------------------------------
@router.get("/nearby")
async def nearby_stores(
    product_variant_id: str,
    lat: float,
    lng: float,
    limit: int = Query(5, ge=1, le=10),
):
    """
    Used by agent:
    "This is available in Store X, 2.1 km away"
    """
    stores = StoreService.find_nearest_stores(lat, lng, limit=limit)

    results = []
    for s in stores:
        inv = (
            supabase.table("inventory")
            .select("quantity_on_hand")
            .eq("product_variant_id", product_variant_id)
            .eq("fulfillment_location_id", s["fulfillment_location_id"])
            .maybe_single()
            .execute()
        ).data

        if inv and inv["quantity_on_hand"] > 0:
            results.append(
                {
                    "store_id": s["id"],
                    "name": s["name"],
                    "distance_km": s["distance_km"],
                    "available_qty": inv["quantity_on_hand"],
                }
            )

    return results

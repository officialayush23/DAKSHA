from fastapi import APIRouter, HTTPException
from app.database import supabase

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/check")
async def check_stock(sku: str, store_id: str):
    """
    Returns stock info for a given SKU at a specific store.
    Used by kiosks, web, and agents.
    """
    variant = (
        supabase.table("product_variants")
        .select("id")
        .eq("sku", sku)
        .maybe_single()
        .execute()
    )
    if not variant.data:
        raise HTTPException(404, "SKU not found")

    stock = (
        supabase.table("inventory")
        .select("quantity_on_hand, quantity_reserved, aisle_number, bay_number, shelf_height, display_location")
        .eq("product_variant_id", variant.data["id"])
        .eq("store_id", store_id)
        .maybe_single()
        .execute()
    )

    if not stock.data:
        return {
            "status": "out_of_stock",
            "qty": 0,
            "location": None,
        }

    data = stock.data
    return {
        "status": "available" if data["quantity_on_hand"] > 0 else "out_of_stock",
        "qty": data["quantity_on_hand"],
        "reserved": data.get("quantity_reserved", 0),
        "location": {
            "aisle": data.get("aisle_number"),
            "bay": data.get("bay_number"),
            "shelf_height": data.get("shelf_height"),
            "display_location": data.get("display_location"),
        },
    }


@router.get("/store/{store_id}")
async def list_store_inventory(store_id: str, limit: int = 100, offset: int = 0):
    """
    Store inventory listing. Used by dashboards and potentially kiosk search.
    """
    res = (
        supabase.table("inventory")
        .select("*, product_variants(sku, color_name, size_label, products(name))")
        .eq("store_id", store_id)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return res.data

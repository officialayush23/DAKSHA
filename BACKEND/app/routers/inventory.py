from fastapi import APIRouter, HTTPException
from app.database import supabase

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/check")
async def check_stock(sku: str, store_id: str):
    variant = (
        supabase.table("product_variants")
        .select("id")
        .eq("sku", sku)
        .single()
        .execute()
    )
    if not variant.data:
        raise HTTPException(404, "SKU not found")

    stock = (
        supabase.table("inventory")
        .select("quantity_on_hand, display_location")
        .eq("product_variant_id", variant.data["id"])
        .eq("store_id", store_id)
        .single()
        .execute()
    )

    qty = stock.data["quantity_on_hand"] if stock.data else 0
    return {
        "status": "available" if qty > 0 else "out_of_stock",
        "qty": qty,
        "location": stock.data.get("display_location") if stock.data else None,
    }

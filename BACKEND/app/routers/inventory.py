from fastapi import APIRouter
from app.services.commerce_service import CommerceService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/check")
async def check_stock(sku: str, store_id: str):
    """
    Returns stock info for a given SKU at a specific store.

    Shape (from CommerceService.get_stock_by_sku):
    {
      "sku": "...",
      "product_name": "...",
      "store_id": "...",
      "available": bool,
      "status": "available" | "out_of_stock",
      "quantity_on_hand": int,
      "quantity_reserved": int,
      "qty": int,         # alias for quantity_on_hand (backward compat)
      "reserved": int,    # alias for quantity_reserved (backward compat)
      "location": {
        "aisle_number": int | null,
        "bay_number": int | null,
        "shelf_height": int | null,
        "display_location": str | null,
        "section_id": uuid | null
      }
    }
    """
    return CommerceService.get_stock_by_sku(sku, store_id)


@router.get("/store/{store_id}")
async def list_store_inventory(store_id: str, limit: int = 100, offset: int = 0):
    """
    Store inventory listing for a given store.

    Delegates to CommerceService.list_store_inventory so dashboards,
    kiosks and future agents stay consistent.
    """
    return CommerceService.list_store_inventory(store_id=store_id, limit=limit, offset=offset)

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from app.database import supabase
from app.core.rbac import require_store_access
from app.models.management import StockUpdate
from datetime import datetime, timezone
import logging

logger = logging.getLogger("admin.inventory")
router = APIRouter(prefix="/admin/inventory", tags=["Admin: Store Ops"])

# ---------------------------------------------------------
# 📊 DASHBOARD
# ---------------------------------------------------------
@router.get("/dashboard/{store_id}")
async def get_store_dashboard(
    store_id: str = Path(...),
    include_graphs: bool = Query(False),
    _rbac = Depends(require_store_access("store_id")),
):
    try:
        # 1. Get Fulfillment Location
        store_res = supabase.table("stores").select("fulfillment_location_id").eq("id", store_id).maybe_single().execute()
        
        if not store_res or not store_res.data:
            return {"store_id": store_id, "error": "Store not found or no data returned"}
        
        fl_id = store_res.data.get('fulfillment_location_id')
        if not fl_id:
            return {"store_id": store_id, "total_items": 0, "low_stock_count": 0, "pending_orders": 0, "todays_revenue": 0}

        # 2. Stats
        inv_count = supabase.table("inventory").select("id", count="exact", head=True).eq("fulfillment_location_id", fl_id).execute().count or 0
        low_stock = supabase.table("inventory").select("id", count="exact", head=True).eq("fulfillment_location_id", fl_id).lt("quantity_on_hand", 10).execute().count or 0
        pending = supabase.table("orders").select("id", count="exact", head=True).eq("store_id", store_id).eq("status", "pending").execute().count or 0

        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        rev_res = supabase.table("orders").select("total_amount").eq("store_id", store_id).gte("created_at", today).execute()
        revenue = sum(r['total_amount'] for r in rev_res.data) if rev_res.data else 0

        return {
            "store_id": store_id,
            "total_items": inv_count,
            "low_stock_count": low_stock,
            "pending_orders": pending,
            "todays_revenue": revenue
        }
    except Exception as e:
        logger.error(f"Dashboard failed: {e}")
        return {"store_id": store_id, "total_items": 0, "low_stock_count": 0, "pending_orders": 0, "todays_revenue": 0}

# ---------------------------------------------------------
# 📥 INWARD STOCK (Fixed: Removed updated_at)
# ---------------------------------------------------------
@router.post("/inward/{store_id}")
async def inward_stock(
    data: StockUpdate, 
    store_id: str = Path(...),
    _rbac = Depends(require_store_access("store_id"))
):
    try:
        # 1. Resolve Store
        store_res = supabase.table("stores").select("fulfillment_location_id").eq("id", store_id).maybe_single().execute()
        
        if not store_res.data:
             raise HTTPException(404, "Store not found")
             
        fl_id = store_res.data.get('fulfillment_location_id')
        if not fl_id:
             raise HTTPException(400, "Store has no linked Fulfillment Location. Contact Super Admin.")

        # 2. Get Current Inventory
        existing = supabase.table("inventory").select("quantity_on_hand")\
            .eq("fulfillment_location_id", fl_id)\
            .eq("product_variant_id", data.product_variant_id)\
            .maybe_single().execute()
        
        current_qty = existing.data['quantity_on_hand'] if (existing and existing.data) else 0
        new_qty = current_qty + data.quantity

        # 3. UPSERT
        payload = {
            "fulfillment_location_id": fl_id,
            "product_variant_id": data.product_variant_id,
            "quantity_on_hand": new_qty,
            "aisle_number": data.aisle,
            "shelf_height": data.shelf,
            # "updated_at": "now()" <--- REMOVED THIS to fix Schema Cache Error
        }
        
        res = supabase.table("inventory").upsert(
            payload, on_conflict="fulfillment_location_id, product_variant_id"
        ).execute()

        # 4. SAFETY FETCH
        if not res.data:
            final_res = supabase.table("inventory").select("*")\
                .eq("fulfillment_location_id", fl_id)\
                .eq("product_variant_id", data.product_variant_id)\
                .single().execute()
            record = final_res.data
        else:
            record = res.data[0]

        return {"status": "success", "new_quantity": new_qty, "record": record}

    except Exception as e:
        print(f"❌ INWARD EXCEPTION: {e}") 
        raise HTTPException(500, detail=f"Server Error: {str(e)}")

# ---------------------------------------------------------
# 📋 ORDERS
# ---------------------------------------------------------
@router.get("/orders/{store_id}")
async def get_store_orders(
    store_id: str = Path(...), 
    tab: str = Query("new"), 
    _rbac = Depends(require_store_access("store_id"))
):
    try:
        status_map = {
            "new": ["pending", "paid"],
            "processing": ["processing"],
            "completed": ["shipped", "delivered"],
            "cancelled": ["cancelled", "returned"]
        }
        statuses = status_map.get(tab, ["pending"])

        res = supabase.table("orders").select(
            "*, order_items(*, product_variants(*, products(name))), users(full_name)"
        ).eq("store_id", store_id).in_("status", statuses).order("created_at", desc=True).execute()
        
        return res.data or []
    except Exception:
        return []

@router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, payload: dict):
    res = supabase.table("orders").update({"status": payload["status"]}).eq("id", order_id).execute()
    return {"status": "updated"}

# ---------------------------------------------------------
# 📦 INVENTORY LIST
# ---------------------------------------------------------
@router.get("/items/{store_id}")
async def get_inventory_list(store_id: str = Path(...), _rbac = Depends(require_store_access("store_id"))):
    try:
        store = supabase.table("stores").select("fulfillment_location_id").eq("id", store_id).maybe_single().execute()
        if not store or not store.data: return []
        
        fl_id = store.data.get('fulfillment_location_id')
        if not fl_id: return []
        
        res = supabase.table("inventory").select(
            "*, product_variants!inner(*, products!inner(name))"
        ).eq("fulfillment_location_id", fl_id).execute()
        
        return [
            {
                "id": i['id'], "quantity_on_hand": i['quantity_on_hand'], 
                "aisle_number": i['aisle_number'], "shelf_height": i['shelf_height'],
                "variant": i['product_variants'], "product": i['product_variants']['products']
            } for i in res.data or []
        ]
    except Exception as e:
        print(f"List Error: {e}")
        return []

# ---------------------------------------------------------
# 🔍 SEARCH HELPERS
# ---------------------------------------------------------
@router.get("/products/search")
async def search_catalog(q: str = ""):
    query = supabase.table("products").select("id, name, base_price").limit(10)
    if q: query = query.ilike("name", f"%{q}%")
    return query.execute().data or []

@router.get("/products/{product_id}/variants")
async def get_catalog_variants(product_id: str):
    return supabase.table("product_variants").select("*").eq("product_id", product_id).execute().data or []
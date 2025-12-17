# from fastapi import APIRouter, Depends, Query, HTTPException
# from app.models.management import StoreCreate, InventoryFullUpdate
# from app.database import supabase
# from app.services.inventory_service import InventoryService
# from app.core.rbac import require_role, require_store_access
# from datetime import datetime, timezone
# from typing import Optional
# import traceback
# router = APIRouter(prefix="/admin/inventory", tags=["Admin: Store Ops"])


# # ---------------------------------------------------------
# # CREATE STORE / WAREHOUSE (SUPER ADMIN ONLY)
# # ---------------------------------------------------------
# @router.post("/stores")
# async def create_store(
#     data: StoreCreate,
#     _rbac = Depends(require_role("super_admin")),
# ):
#     loc = (
#         supabase.table("fulfillment_locations")
#         .insert(
#             {
#                 "type": data.type,
#                 "name": data.name,
#                 "city": data.city,
#                 "latitude": data.latitude,
#                 "longitude": data.longitude,
#                 "address_line": data.address_line_1,
#             }
#         )
#         .execute()
#     ).data[0]

#     store = (
#         supabase.table("stores")
#         .insert(
#             {
#                 "store_code": data.store_code,
#                 "name": data.name,
#                 "type": data.type,
#                 "city": data.city,
#                 "address_line_1": data.address_line_1,
#                 "latitude": data.latitude,
#                 "longitude": data.longitude,
#                 "fulfillment_location_id": loc["id"],
#             }
#         )
#         .execute()
#     ).data[0]

#     return {"store": store, "fulfillment_location": loc}


# # ---------------------------------------------------------
# # DASHBOARD
# # ---------------------------------------------------------
# @router.get("/dashboard/{store_id}")
# async def get_store_dashboard(
#     store_id: str,
#     _rbac = Depends(require_store_access("store_id")),
# ):
#     return InventoryService.get_store_dashboard(store_id)


# # ---------------------------------------------------------
# # INVENTORY UPDATE
# # ---------------------------------------------------------
# @router.patch("/update")
# async def update_inventory_details(
#     data: InventoryFullUpdate,
#     _rbac = Depends(require_store_access("store_id")),
# ):
#     updated = await InventoryService.full_update(data)
#     return {"status": "updated", "data": updated}





import traceback
from fastapi import APIRouter, Depends, Query, HTTPException
from app.models.management import StoreCreate, InventoryFullUpdate
from app.database import supabase
from app.services.inventory_service import InventoryService
from app.core.rbac import require_role, require_store_access
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/inventory", tags=["Admin: Store Ops"])


class OrderStatusUpdate(BaseModel):
    status: str

# ---------------------------------------------------------
# GET ORDERS FOR QUEUE
# ---------------------------------------------------------
@router.get("/orders/{store_id}")
async def get_store_orders(store_id: str, tab: str = "new",
                            _rbac = Depends(require_store_access("store_id"))):
    """
    Fetches orders for a specific store, filtered by the 'Tab' 
    (new, processing, completed, cancelled).
    """
    try:
        # 1. Map 'Tab' to specific Statuses
        status_filter = []
        if tab == 'new':
            status_filter = ['pending', 'paid']
        elif tab == 'processing':
            status_filter = ['processing']
        elif tab == 'completed':
            status_filter = ['shipped', 'delivered']
        elif tab == 'cancelled':
            status_filter = ['cancelled', 'returned']

        # 2. Build Query
        query = supabase.table("orders").select(
            """
            id, status, total_amount, created_at, type, user_id,
            order_items (
                id, quantity, price_at_purchase,
                product_variants (
                    sku, size_label, color_name,
                    products ( name )
                )
            )
            """
        )\
        .eq("store_id", store_id)\
        .in_("status", status_filter)\
        .order("created_at", desc=True)

        res = query.execute()
        return res.data

    except Exception as e:
        print(f"❌ Order Fetch Error: {e}")
        return []

# ---------------------------------------------------------
# UPDATE ORDER STATUS
# ---------------------------------------------------------
@router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, data: OrderStatusUpdate, _rbac = Depends(require_store_access("store_id")),):
    """
    Updates the status of an order (e.g., pending -> processing -> shipped).
    """
    try:
        res = supabase.table("orders")\
            .update({"status": data.status})\
            .eq("id", order_id)\
            .execute()
            
        if not res.data:
            raise HTTPException(status_code=404, detail="Order not found")
            
        return {"status": "success", "data": res.data[0]}

    except Exception as e:
        print(f"❌ Order Update Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ---------------------------------------------------------
# CREATE STORE / WAREHOUSE (SUPER ADMIN ONLY)
# ---------------------------------------------------------
@router.post("/stores")
async def create_store(
    data: StoreCreate,
    _rbac = Depends(require_role("super_admin")),
):
    # 1. Create entry in fulfillment_locations (Polymorphic parent)
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

    # 2. Create entry in stores (Specific details)
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
# DASHBOARD (FIXED: No 'kwargs')
# ---------------------------------------------------------
@router.get("/dashboard/{store_id}")
async def get_store_dashboard(
    store_id: str,
    include_graphs: bool = Query(False),
    _rbac = Depends(require_store_access("store_id")),
):
    """
    Fetches real-time stats for the Store Dashboard.
    Smart Logic: Tries to find the correct Location ID. 
    If that fails (Access Denied), falls back to store_id to prevent crashing.
    """
    try:
        # -------------------------------------------------------
        # 1. ATTEMPT ID LOOKUP (Fixes the "All Zeros" issue)
        # -------------------------------------------------------
        actual_location_id = store_id  # Default fallback
        
        try:
            # Try to get the real location ID from the stores table
            store_res = supabase.table("stores")\
                .select("fulfillment_location_id")\
                .eq("id", store_id)\
                .limit(1)\
                .execute()
                
            if store_res.data and len(store_res.data) > 0:
                actual_location_id = store_res.data[0]['fulfillment_location_id']
                print(f"✅ ID Fixed: Store {store_id} -> Location {actual_location_id}")
            else:
                print(f"⚠️ Store ID lookup returned empty. Using {store_id} as fallback.")

        except Exception as lookup_error:
            # If RLS blocks this, we just log it and continue with the original ID
            # This prevents the "Access Denied" crash you saw
            print(f"⚠️ Could not resolve Location ID (likely RLS permissions): {lookup_error}")
            actual_location_id = store_id

        # -------------------------------------------------------
        # 2. FETCH STATS (Using the resolved ID)
        # -------------------------------------------------------

        # A. Total Inventory Count
        inv_res = supabase.table("inventory")\
            .select("id", count="exact")\
            .eq("fulfillment_location_id", actual_location_id)\
            .execute()
        total_items = inv_res.count if inv_res.count is not None else 0

        # B. Low Stock Count (Threshold < 10)
        low_stock_res = supabase.table("inventory")\
            .select("id", count="exact")\
            .eq("fulfillment_location_id", actual_location_id)\
            .lt("quantity_on_hand", 10)\
            .execute()
        low_stock_count = low_stock_res.count if low_stock_res.count is not None else 0

        # C. Pending Orders (Orders are linked to STORE ID, not Location ID)
        pending_res = supabase.table("orders")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .eq("status", "pending")\
            .execute()
        pending_orders = pending_res.count if pending_res.count is not None else 0

        # D. Today's Revenue
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        revenue_res = supabase.table("orders")\
            .select("total_amount")\
            .eq("store_id", store_id)\
            .gte("created_at", today_str)\
            .execute()
        
        todays_revenue = 0
        if revenue_res.data:
            todays_revenue = sum(item['total_amount'] for item in revenue_res.data)

        return {
            "store_id": store_id,
            "total_items": total_items,
            "low_stock_count": low_stock_count,
            "pending_orders": pending_orders,
            "todays_revenue": todays_revenue
        }

    except Exception as e:
        print(f"❌ Dashboard Fatal Error: {e}")
        # Return fallback zeros so frontend loads
        return {
            "store_id": store_id,
            "total_items": 0,
            "low_stock_count": 0,
            "pending_orders": 0,
            "todays_revenue": 0
        }


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

# ---------------------------------------------------------
# GET INVENTORY LIST (REQUIRED FOR TABLE VIEW)
# ---------------------------------------------------------
# app/routers/admin_inventory.py

@router.get("/items/{store_id}")
async def get_store_inventory_list(store_id: str,
                                    _rbac = Depends(require_store_access("store_id")),):
    """
    Fetches the inventory list.
    FIX: Looks up the correct 'fulfillment_location_id' before querying inventory.
    """
    try:
        # 1. CRITICAL STEP: Convert Store ID -> Fulfillment Location ID
        # The frontend sends 'store_id', but inventory table uses 'fulfillment_location_id'
        store_res = supabase.table("stores")\
            .select("fulfillment_location_id")\
            .eq("id", store_id)\
            .limit(1)\
            .execute()

        if not store_res.data:
            print("❌ Store not found")
            return []

        # This is the ID that actually exists in your inventory table
        actual_location_id = store_res.data[0]['fulfillment_location_id']
        
        print(f"🔍 Searching Inventory for Location ID: {actual_location_id}")

        # 2. QUERY INVENTORY using the CORRECT ID
        response = supabase.table("inventory").select(
            """
            id, quantity_on_hand, aisle_number, shelf_height,
            product_variants!inner (
                sku, color_name, size_label, image_url,
                products!inner ( name, category_id )
            )
            """
        ).eq("fulfillment_location_id", actual_location_id)\
         .order("quantity_on_hand", desc=False)\
         .execute()

        # 3. Format Data
        clean_data = []
        for item in response.data:
            variant_data = item.get('product_variants', {})
            product_data = variant_data.get('products', {})
            
            clean_data.append({
                "id": item['id'],
                "quantity_on_hand": item['quantity_on_hand'],
                "aisle_number": item['aisle_number'],
                "shelf_height": item['shelf_height'],
                "variant": {
                    "sku": variant_data.get('sku'),
                    "color_name": variant_data.get('color_name'),
                    "size_label": variant_data.get('size_label'),
                    "image_url": variant_data.get('image_url')
                },
                "product": {
                    "name": product_data.get('name')
                }
            })
            
        return clean_data

    except Exception as e:
        print(f"❌ Inventory List Error: {e}")
        return []

# app/routers/admin_inventory.py

# ... existing imports ..

# --- SCHEMA FOR INWARDING ---
class StockUpdate(BaseModel):
    product_variant_id: str
    quantity: int
    aisle: Optional[int] = None
    shelf: Optional[int] = None

# --- MINIMAL ENDPOINTS ---

# 1. SEARCH (Read-Only from Catalog)
@router.get("/products/search")
async def search_catalog_products(q: str = ""):
    """
    Search global products created by Catalog Admins.
    """
    try:
        query = supabase.table("products").select("id, name, category_id").limit(20)
        if q:
            query = query.ilike("name", f"%{q}%")
        else:
            query = query.order("name", desc=False)
        return query.execute().data
    except Exception:
        return []

# 2. GET VARIANTS (Read-Only from Catalog)
@router.get("/products/{product_id}/variants")
async def get_catalog_variants(product_id: str):
    """
    Get valid SKUs/Sizes/Colors for a product.
    """
    try:
        return supabase.table("product_variants").select("*").eq("product_id", product_id).execute().data
    except Exception:
        return []
    
@router.post("/inward/{store_id}")
async def inward_stock(store_id: str, data: StockUpdate,
                        _rbac = Depends(require_store_access("store_id")),):
    """
    Inward Stock. 
    Fixes Foreign Key Error by looking up the correct fulfillment_location_id.
    """
    try:
        # 1. CRITICAL LOOKUP: Get the actual Fulfillment Location ID for this Store
        # The frontend sends 'stores.id', but inventory needs 'fulfillment_locations.id'
        store_res = supabase.table("stores")\
            .select("fulfillment_location_id")\
            .eq("id", store_id)\
            .limit(1)\
            .execute()

        if not store_res.data:
            raise HTTPException(status_code=404, detail="Store not found in database")
            
        # This is the ID we must use for the inventory table
        actual_location_id = store_res.data[0]['fulfillment_location_id']

        if not actual_location_id:
             raise HTTPException(status_code=500, detail="Store has no linked Fulfillment Location ID")

        # 2. VALIDATION: Check if Variant exists
        variant_check = supabase.table("product_variants")\
            .select("id")\
            .eq("id", data.product_variant_id)\
            .execute()
            
        if not variant_check.data:
            raise HTTPException(status_code=404, detail="Product Variant not found in catalog")

        # 3. PROCEED: Update or Insert using the CORRECT LOCATION ID
        res = supabase.table("inventory")\
            .select("id, quantity_on_hand")\
            .eq("product_variant_id", data.product_variant_id)\
            .eq("fulfillment_location_id", actual_location_id)\
            .limit(1)\
            .execute()
        
        existing_item = res.data[0] if res.data else None

        if existing_item:
            # Update existing
            current_qty = existing_item.get('quantity_on_hand') or 0
            new_qty = current_qty + data.quantity
            
            payload = {"quantity_on_hand": new_qty}
            if data.aisle is not None: payload["aisle_number"] = data.aisle
            if data.shelf is not None: payload["shelf_height"] = data.shelf
            
            supabase.table("inventory").update(payload).eq("id", existing_item['id']).execute()
            return {"status": "updated", "new_total": new_qty}
        else:
            # Insert new
            payload = {
                "product_variant_id": data.product_variant_id,
                "fulfillment_location_id": actual_location_id, # <--- Using the correct ID
                "quantity_on_hand": data.quantity,
                "aisle_number": data.aisle,
                "shelf_height": data.shelf
            }
            supabase.table("inventory").insert(payload).execute()
            return {"status": "created", "new_total": data.quantity}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
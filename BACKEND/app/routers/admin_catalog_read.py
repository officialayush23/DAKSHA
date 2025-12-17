# app/routers/admin_catalog_read.py


from app.database import supabase
from app.core.rbac import require_role
from fastapi import APIRouter, Depends, HTTPException, Query
router = APIRouter(
    prefix="/admin/catalog/read",
    tags=["Admin: Catalog Read"]
)

# -----------------------------------
# LIST PRODUCTS
# -----------------------------------

@router.get("/products")
async def get_products_list(
    q: str = Query(None),
    limit: int = 50,
    admin = Depends(require_role("catalog_admin"))
):
    try:
        query = supabase.table("products")\
            .select("*, categories(name)")\
            .order("created_at", desc=True)\
            .limit(limit)

        if q:
            query = query.ilike("name", f"%{q}%")

        res = query.execute()
        return res.data

    except Exception as e:
        print(f"Product List Error: {e}")
        return []

# -----------------------------------
# PRODUCT DETAIL (with variants)
# -----------------------------------
@router.get("/products/{product_id}")
async def get_product_details(product_id: str, admin = Depends(require_role("catalog_admin"))):
    """
    Fetches details for a single product (used in Create Variant page).
    """
    try:
        res = supabase.table("products")\
            .select("*, categories(name)")\
            .eq("id", product_id)\
            .limit(1)\
            .execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return res.data[0]
    except Exception as e:
        print(f"Fetch Product Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load product")


# -----------------------------------
# LIST VARIANTS (Global)
# -----------------------------------
@router.get("/variants")
async def list_variants(
    _rbac=Depends(require_role("catalog_admin")),
):
    return (
        supabase.table("product_variants")
        .select(
            """
            id, sku, product_id,
            color_name, size_label,
            material, price_override,
            created_at
            """
        )
        .order("created_at", desc=True)
        .execute()
        .data
    )


# -----------------------------------
# CATEGORY TREE
# -----------------------------------
@router.get("/categories")
async def get_categories(admin = Depends(require_role("catalog_admin"))):
    """
    Fetch all categories for the product creation dropdown.
    """
    try:
        res = supabase.table("categories").select("id, name").order("name").execute()
        return res.data
    except Exception as e:
        print(f"Category Fetch Error: {e}")
        return []


@router.get("/products/{product_id}/variants")
async def get_product_variants(product_id: str, admin = Depends(require_role("catalog_admin"))):
    """
    Fetches all variants (SKUs) for a specific parent product.
    """
    try:
        res = supabase.table("product_variants")\
            .select("*")\
            .eq("product_id", product_id)\
            .order("created_at", desc=True)\
            .execute()
        return res.data
    except Exception as e:
        print(f"Fetch Variants Error: {e}")
        return []



@router.get("/dashboard")
async def get_catalog_dashboard(admin = Depends(require_role("catalog_admin"))):
    """
    Fetches dashboard stats.
    FIX: 'Missing Images' now correctly counts NULLs.
    """
    try:
        # 1. Total Products
        p_count = supabase.table("products").select("id", count="exact", head=True).execute()
        total_products = p_count.count or 0

        # 2. Total Variants
        v_count = supabase.table("product_variants").select("id", count="exact", head=True).execute()
        total_variants = v_count.count or 0

        # 3. Total Categories
        c_count = supabase.table("categories").select("id", count="exact", head=True).execute()
        total_categories = c_count.count or 0
        
        # 4. Missing Images (Variants where image_url is NULL)
        # Note: We use 'head=True' to only get the count, not the data
        missing_res = supabase.table("product_variants")\
            .select("id", count="exact", head=True)\
            .is_("image_url", "null")\
            .execute()
        
        missing_images = missing_res.count or 0

        # 5. Recent Products
        recent_res = supabase.table("products")\
            .select("id, name, base_price, created_at, categories(name)")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()

        # 6. Quick Categories
        cat_res = supabase.table("categories")\
            .select("name, slug")\
            .limit(5)\
            .execute()

        return {
            "stats": {
                "total_products": total_products,
                "total_variants": total_variants,
                "total_categories": total_categories,
                "missing_images": missing_images
            },
            "recent_products": recent_res.data or [],
            "categories": cat_res.data or []
        }

    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        # Return zeros on error to keep UI alive
        return {
            "stats": { "total_products": 0, "total_variants": 0, "total_categories": 0, "missing_images": 0 },
            "recent_products": [],
            "categories": []
        }
    




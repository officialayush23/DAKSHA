from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user_id
from app.models.management import ProductCreate, VariantCreate, CategoryCreate
from app.services.ai_service import AIService
from app.database import supabase
from app.core.rbac import require_role

router = APIRouter(prefix="/admin/catalog", tags=["Admin: Catalog"])

# ==============================================================================
# 📊 DASHBOARD
# ==============================================================================

@router.get("/dashboard")
async def get_catalog_dashboard(admin = Depends(require_role("catalog_admin"))):
    """
    Fetches stats for the Catalog Dashboard.
    """
    try:
        # 1. Counts (Head requests for performance)
        p_count = supabase.table("products").select("id", count="exact", head=True).execute()
        v_count = supabase.table("product_variants").select("id", count="exact", head=True).execute()
        c_count = supabase.table("categories").select("id", count="exact", head=True).execute()
        
        # 2. Missing Images Count
        missing_res = supabase.table("product_variants").select("id", count="exact", head=True).is_("image_url", "null").execute()
        
        # 3. Recent Products
        recent_res = supabase.table("products")\
            .select("id, name, base_price, created_at, categories(name)")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()

        # 4. Quick Categories
        cat_res = supabase.table("categories").select("name, slug").limit(5).execute()

        return {
            "stats": {
                "total_products": p_count.count or 0,
                "total_variants": v_count.count or 0,
                "total_categories": c_count.count or 0,
                "missing_images": missing_res.count or 0
            },
            "recent_products": recent_res.data or [],
            "categories": cat_res.data or []
        }
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        return {"stats": {}, "recent_products": [], "categories": []}

# ==============================================================================
# 📦 PRODUCTS
# ==============================================================================

@router.get("/products")
async def list_products(
    q: Optional[str] = None, 
    limit: int = 50,
    admin = Depends(require_role("catalog_admin"))
):
    """
    List products with optional search.
    """
    query = supabase.table("products").select("*, categories(name)").order("created_at", desc=True).limit(limit)
    if q:
        query = query.ilike("name", f"%{q}%")
    return query.execute().data

@router.get("/products/{product_id}")
async def get_product_details(product_id: str, admin = Depends(require_role("catalog_admin"))):
    """
    Get single product details.
    """
    res = supabase.table("products").select("*, categories(name)").eq("id", product_id).maybe_single().execute()
    if not res.data:
        raise HTTPException(404, "Product not found")
    return res.data

@router.post("/products")
async def create_product(data: ProductCreate, admin = Depends(require_role("catalog_admin"))):
    """
    Create a new product parent.
    """
    try:
        # Generate embedding for AI search
        embedding = AIService.generate_embedding(
            f"{data.name} {data.description} {' '.join(data.style_tags)}"
        )
        
        payload = data.dict()
        payload["is_active"] = True
        payload["description_embedding"] = embedding 
        
        res = supabase.table("products").insert(payload).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(500, detail=f"Create Product Failed: {str(e)}")

@router.patch("/products/{product_id}/status")
async def toggle_product_status(product_id: str, admin = Depends(require_role("catalog_admin"))):
    """
    Toggle is_active status.
    """
    curr = supabase.table("products").select("is_active").eq("id", product_id).maybe_single().execute()
    if not curr.data:
        raise HTTPException(404, "Product not found")
        
    new_status = not curr.data['is_active']
    res = supabase.table("products").update({"is_active": new_status}).eq("id", product_id).execute()
    return res.data[0]

# ==============================================================================
# 🎨 VARIANTS
# ==============================================================================

@router.get("/products/{product_id}/variants")
async def get_product_variants(product_id: str, admin = Depends(require_role("catalog_admin"))):
    """
    Get all variants for a specific product.
    """
    return supabase.table("product_variants").select("*").eq("product_id", product_id).order("created_at", desc=True).execute().data

@router.post("/variants")
async def create_variant(data: VariantCreate, admin = Depends(require_role("catalog_admin"))):
    """
    Create a new SKU.
    """
    # Check duplicate SKU
    exists = supabase.table("product_variants").select("id").eq("sku", data.sku).maybe_single().execute()
    if exists.data:
        raise HTTPException(400, f"SKU '{data.sku}' already exists.")
        
    try:
        res = supabase.table("product_variants").insert(data.dict()).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.delete("/variants/{variant_id}")
async def delete_variant(variant_id: str, admin = Depends(require_role("catalog_admin"))):
    """
    Delete a SKU.
    """
    supabase.table("product_variants").delete().eq("id", variant_id).execute()
    return {"status": "deleted"}

# ==============================================================================
# 🏷️ CATEGORIES
# ==============================================================================

@router.get("/categories")
async def get_categories(admin = Depends(require_role("catalog_admin"))):
    """
    List all categories.
    """
    return supabase.table("categories").select("*").order("name").execute().data

@router.post("/categories")
async def create_category(data: CategoryCreate, admin = Depends(require_role("catalog_admin"))):
    """
    Create a new category.
    """
    # Check slug uniqueness
    exists = supabase.table("categories").select("id").eq("slug", data.slug).maybe_single().execute()
    if exists.data:
        raise HTTPException(400, f"Slug '{data.slug}' already exists.")
        
    res = supabase.table("categories").insert(data.dict()).execute()
    return res.data[0]
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.database import supabase
from app.core.auth import get_current_user_id # Using your provided auth module

router = APIRouter(prefix="/admin/catalog", tags=["Admin: Catalog"])

# ---------------------------------------------------------
# 🔒 SECURITY DEPENDENCY (RBAC)
# ---------------------------------------------------------
async def verify_catalog_admin(user_id: str = Depends(get_current_user_id)):
    """
    Validates that the user has the 'catalog_admin' role 
    in the public.user_roles table.
    """
    try:
        # 1. Query the 'user_roles' table, NOT the 'users' table
        res = supabase.table("user_roles")\
            .select("role")\
            .eq("user_id", user_id)\
            .execute()
        
        # 2. Extract roles list (A user might have multiple roles)
        # Example: ['store_manager', 'catalog_admin']
        user_roles = [item['role'] for item in res.data]
        
        # 3. Check for specific Catalog permissions
        # We allow 'catalog_admin' OR 'super_admin' (if you have one)
        allowed_roles = ["catalog_admin", "super_admin"]
        
        # Check if any of the user's roles are in the allowed list
        has_access = any(role in allowed_roles for role in user_roles)
        
        if not has_access:
            print(f"⛔ Access Denied: User {user_id} has roles {user_roles}, but needs {allowed_roles}")
            raise HTTPException(
                status_code=403, 
                detail="Access Denied. You do not have Catalog Admin privileges."
            )
            
        return user_id

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"RBAC Error: {e}")
        raise HTTPException(status_code=500, detail="Role verification failed.")
# ---------------------------------------------------------
# SCHEMAS (Pydantic Models)
# ---------------------------------------------------------
class ProductCreate(BaseModel):
    name: str
    description: str
    category_id: str
    base_price: float
    gender: str
    season: str = "all_season"
    usage_type: str = "casual"
    style_tags: List[str] = []

class VariantCreate(BaseModel):
    product_id: str
    sku: str
    size_label: str
    color_name: str
    color_hex: Optional[str] = "#000000"
    # --- NEW FIELDS MATCHING DB ---
    material: Optional[str] = None
    pattern: Optional[str] = None
    fit_type: Optional[str] = None
    price_override: Optional[float] = None
    image_url: Optional[str] = None
    attributes: Optional[dict] = {} # For the jsonb field

# ---------------------------------------------------------
# 1. GET CATEGORIES (For Dropdown)
# ---------------------------------------------------------
@router.get("/categories")
async def get_categories(admin = Depends(verify_catalog_admin)):
    """
    Fetch all categories for the product creation dropdown.
    """
    try:
        res = supabase.table("categories").select("id, name").order("name").execute()
        return res.data
    except Exception as e:
        print(f"Category Fetch Error: {e}")
        return []

# ---------------------------------------------------------
# 2. CREATE PRODUCT
# ---------------------------------------------------------
@router.post("/products")
async def create_product(
    data: ProductCreate, 
    admin = Depends(verify_catalog_admin)
):
    """
    Creates a new Parent Product.
    """
    try:
        payload = {
            "name": data.name,
            "description": data.description,
            "category_id": data.category_id,
            "base_price": data.base_price,
            "gender": data.gender,
            "season": data.season,
            "usage_type": data.usage_type,
            "style_tags": data.style_tags,
            "is_active": True
        }
        
        # Fix: Just .execute(), do not chain .select()
        res = supabase.table("products").insert(payload).execute()
        
        if not res.data:
            raise HTTPException(status_code=400, detail="Failed to insert product")
            
        return res.data[0]
        
    except Exception as e:
        print(f"Create Product Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 3. CREATE VARIANT
# ---------------------------------------------------------
@router.post("/variants")
async def create_variant(
    data: VariantCreate,
    admin = Depends(verify_catalog_admin),
):
    """
    Adds a physical SKU to a product with full details.
    """
    try:
        # Check uniqueness
        exists = (
            supabase.table("product_variants")
            .select("id")
            .eq("sku", data.sku)
            .limit(1)
            .execute()
        ).data

        if exists:
            raise HTTPException(400, detail=f"SKU '{data.sku}' already exists")

        # Insert - Pydantic .dict() handles all the fields automatically
        res = supabase.table("product_variants").insert(data.dict()).execute()
        return res.data[0]

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Create Variant Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ---------------------------------------------------------
# 4. CATALOG DASHBOARD (Robust)
# ---------------------------------------------------------
# ---------------------------------------------------------
# CATALOG DASHBOARD (FIXED)
# ---------------------------------------------------------
@router.get("/dashboard")
async def get_catalog_dashboard(admin = Depends(verify_catalog_admin)):
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

# ---------------------------------------------------------
# 5. GET PRODUCT LIST (Search + Filter)
# ---------------------------------------------------------
@router.get("/products")
async def get_products_list(
    q: str = Query(None),
    limit: int = 50,
    admin = Depends(verify_catalog_admin)
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

# ---------------------------------------------------------
# 6. TOGGLE STATUS
# ---------------------------------------------------------
@router.patch("/products/{product_id}/status")
async def toggle_product_status(product_id: str, admin = Depends(verify_catalog_admin)):
    try:
        # Get current
        current = supabase.table("products").select("is_active").eq("id", product_id).limit(1).execute()
        
        if not current.data:
            raise HTTPException(status_code=404, detail="Product not found")

        # Flip status
        new_status = not current.data[0]['is_active']
        
        # Update
        res = supabase.table("products").update({"is_active": new_status}).eq("id", product_id).execute()
        
        return {"status": "success", "new_state": new_status}

    except Exception as e:
        print(f"Status Toggle Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# app/routers/admin_catalog.py

# ... existing imports ...

# ---------------------------------------------------------
# GET SINGLE PRODUCT (For Page Header)
# ---------------------------------------------------------
@router.get("/products/{product_id}")
async def get_product_details(product_id: str, admin = Depends(verify_catalog_admin)):
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

# ---------------------------------------------------------
# GET VARIANTS FOR A PRODUCT (For Table List)
# ---------------------------------------------------------
@router.get("/products/{product_id}/variants")
async def get_product_variants(product_id: str, admin = Depends(verify_catalog_admin)):
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

# ---------------------------------------------------------
# DELETE VARIANT
# ---------------------------------------------------------
@router.delete("/variants/{variant_id}")
async def delete_variant(variant_id: str, admin = Depends(verify_catalog_admin)):
    """
    Deletes a specific variant (SKU).
    """
    try:
        res = supabase.table("product_variants").delete().eq("id", variant_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# app/routers/admin_catalog.py

# ... existing imports ...

# --- SCHEMAS ---
class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: Optional[str] = None

# ... (ProductCreate, VariantCreate schemas) ...

# ---------------------------------------------------------
# GET CATEGORIES (List all)
# ---------------------------------------------------------
@router.get("/categories")
async def get_categories(admin = Depends(verify_catalog_admin)):
    """
    Fetch all categories. Protected by RBAC.
    """
    try:
        # We fetch all fields to build the tree
        res = supabase.table("categories").select("*").order("name").execute()
        return res.data
    except Exception as e:
        print(f"Category Fetch Error: {e}")
        return []

# ---------------------------------------------------------
# CREATE CATEGORY
# ---------------------------------------------------------
@router.post("/categories")
async def create_category(
    data: CategoryCreate, 
    admin = Depends(verify_catalog_admin)
):
    """
    Create a new category node.
    """
    try:
        # Check for duplicates (optional but good practice)
        existing = supabase.table("categories").select("id").eq("slug", data.slug).limit(1).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail=f"Category slug '{data.slug}' already exists.")

        payload = {
            "name": data.name,
            "slug": data.slug,
            "parent_id": data.parent_id
        }
        
        res = supabase.table("categories").insert(payload).execute()
        
        return res.data[0]

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Create Category Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
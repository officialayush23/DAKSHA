# app/routers/admin_catalog.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user_id
from app.models.management import ProductCreate, VariantCreate, CategoryCreate
from app.services.ai_service import AIService
from app.database import supabase
from app.core.rbac import require_role
from pydantic import BaseModel
router = APIRouter(prefix="/admin/catalog", tags=["Admin: Catalog"])


@router.post("/products")
async def create_product(
    data: ProductCreate,
    rbac = Depends(require_role("catalog_admin"))
):
    embedding = AIService.generate_embedding(
        f"{data.name} {data.description} {' '.join(data.style_tags)}"
    )

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



@router.post("/variants")
async def create_variant(
    data: VariantCreate,
    rbac = Depends(require_role("catalog_admin")),
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
# 5. GET PRODUCT LIST (Search + Filter)
# ---------------------------------------------------------

# ---------------------------------------------------------
# 6. TOGGLE STATUS
# ---------------------------------------------------------
@router.patch("/products/{product_id}/status")
async def toggle_product_status(product_id: str, admin = Depends(require_role("catalog_admin"))):
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

# ---------------------------------------------------------
# GET SINGLE PRODUCT (For Page Header)
# ---------------------------------------------------------

# ---------------------------------------------------------
# GET VARIANTS FOR A PRODUCT (For Table List)
# ---------------------------------------------------------

# ---------------------------------------------------------
# DELETE VARIANT
# ---------------------------------------------------------
@router.delete("/variants/{variant_id}")
async def delete_variant(variant_id: str, admin = Depends(require_role("catalog_admin"))):
    """
    Deletes a specific variant (SKU).
    """
    try:
        res = supabase.table("product_variants").delete().eq("id", variant_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# app/routers/admin_catalog.py


# CREATE CATEGORY
# ---------------------------------------------------------
@router.post("/categories")
async def create_category(
    data: CategoryCreate, 
    admin = Depends(require_role("catalog_admin"))
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
# app/routers/catalog.py
from http.client import HTTPException
from fastapi import APIRouter
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService
from pydantic import BaseModel
from app.database import supabase
from typing import List, Optional
from app.core.auth import get_current_user_id 
from app.core.rbac import require_role

router = APIRouter(prefix="/catalog", tags=["Catalog"])

@router.get("/search")
async def search_catalog(q: str, limit: int = 10):
    embedding = AIService.generate_embedding(q)
    results = CatalogService.search_products(q, embedding, limit)
    return {"results": results}

# --- SCHEMAS ---
class ProductCreate(BaseModel):
    name: str
    description: str
    category_id: str
    base_price: float
    gender: str
    style_tags: Optional[List[str]] = []

class VariantCreate(BaseModel):
    product_id: str
    sku: str
    color_name: str
    size_label: str
    image_url: Optional[str] = None

# =========================================================
# 1. CREATE PRODUCT
# =========================================================
@router.post("/products")
async def create_product(
    data: ProductCreate,
    # _rbac = Depends(require_role("catalog_manager")) # Uncomment to enforce RBAC
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
            "style_tags": data.style_tags
        }
        res = supabase.table("products").insert(payload).execute()
        
        if not res.data:
            raise HTTPException(status_code=400, detail="Failed to create product")
            
        return res.data[0]
        
    except Exception as e:
        print(f"Create Product Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================
# 2. CREATE VARIANT
# =========================================================
@router.post("/variants")
async def create_variant(
    data: VariantCreate,
    # _rbac = Depends(require_role("catalog_manager"))
):
    """
    Adds a SKU (Variant) to a Product.
    """
    try:
        # Check Uniqueness of SKU
        check = supabase.table("product_variants").select("id").eq("sku", data.sku).limit(1).execute()
        if check.data:
            raise HTTPException(status_code=400, detail=f"SKU '{data.sku}' already exists.")

        payload = {
            "product_id": data.product_id,
            "sku": data.sku,
            "color_name": data.color_name,
            "size_label": data.size_label,
            "image_url": data.image_url
        }
        res = supabase.table("product_variants").insert(payload).execute()
        
        return res.data[0]

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Create Variant Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# app/routers/admin_catalog.py

from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.models.management import ProductCreate, VariantCreate
from app.services.ai_service import AIService
from app.database import supabase
from app.core.rbac import require_role

router = APIRouter(prefix="/admin/catalog", tags=["Admin: Catalog"])


@router.post("/products")
async def create_product(
    data: ProductCreate,
    rbac = Depends(require_role("catalog_admin", "super_admin"))
):
    embedding = AIService.generate_embedding(
        f"{data.name} {data.description} {' '.join(data.style_tags)}"
    )

    res = supabase.table("products").insert(
        {
            "name": data.name,
            "description": data.description,
            "base_price": data.base_price,
            "category_id": data.category_id,
            "gender": data.gender,
            "usage_type": data.usage_type,
            "style_tags": data.style_tags,
            "description_embedding": embedding,
        }
    ).execute()

    return res.data[0]


@router.post("/variants")
async def create_variant(
    data: VariantCreate,
    user_id: str = Depends(get_current_user_id),
):
    exists = (
        supabase.table("product_variants")
        .select("id")
        .eq("sku", data.sku)
        .maybe_single()
        .execute()
    ).data

    if exists:
        raise HTTPException(400, "SKU already exists")

    res = supabase.table("product_variants").insert(data.dict()).execute()
    return res.data[0]

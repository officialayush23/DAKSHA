from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.management import ProductCreate, VariantCreate
from app.services.ai_service import AIService
from app.database import supabase

router = APIRouter(prefix="/admin/catalog", tags=["Admin: Catalog"])


@router.post("/products")
async def create_product(
    data: ProductCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a product and automatically generate its semantic embedding
    for hybrid search (products.description_embedding).
    """
    context = f"{data.name} {data.description} {' '.join(data.style_tags)}"
    embedding = AIService.generate_embedding(context)

    # Insert product according to schema:
    # products: (category_id, name, description, gender_enum, usage_type,
    #            season, style_tags, base_price, description_embedding, ...)
    payload = {
        "name": data.name,
        "description": data.description,
        "base_price": data.base_price,
        "category_id": data.category_id,
        "gender": data.gender,          # gender_enum in DB
        "usage_type": data.usage_type,
        "style_tags": data.style_tags,
        "description_embedding": embedding,
    }

    res = supabase.table("products").insert(payload).execute()
    product_id = res.data[0]["id"]

    return {"status": "created", "id": product_id}


@router.post("/variants")
async def create_variant(
    data: VariantCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Adds a SKU (size/color/etc.) to an existing product.
    """
    # product_variants matches schema: product_id, sku, color_name, size_label,
    # material, price_override, attributes, image_url, image_embedding...
    res = supabase.table("product_variants").insert(data.dict()).execute()
    variant_id = res.data[0]["id"]

    return {"status": "created", "id": variant_id}

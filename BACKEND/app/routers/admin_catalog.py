from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id

from app.schemas import ProductCreate, VariantCreate
from app.services.ai_service import AIService
from app.database import supabase

router = APIRouter(prefix="/admin/catalog", tags=["Admin: Catalog"])

@router.post("/products")
async def create_product(data: ProductCreate, user_id: str = Depends(get_current_user_id)):
    """
    Creates a product AND automatically generates its AI embedding.
    """
    # 1. Generate Embedding for Semantic Search
    # We combine name + desc + tags to give the AI a full picture
    context = f"{data.name} {data.description} {' '.join(data.style_tags)}"
    embedding = AIService.generate_embedding(context)
    
    # 2. Insert into DB
    res = supabase.table("products").insert({
        **data.dict(),
        "description_embedding": embedding
    }).execute()
    
    return {"status": "created", "id": res.data[0]['id']}

@router.post("/variants")
async def create_variant(data: VariantCreate, user_id: str = Depends(get_current_user_id)):
    """
    Adds a SKU (Size/Color) to a product.
    """
    # In prod, generate image embedding from URL here if available
    res = supabase.table("product_variants").insert(data.dict()).execute()
    return {"status": "created", "id": res.data[0]['id']}
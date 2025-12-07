from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id

from app.services.commerce_service import CommerceService
from app.services.ai_service import AIService
from app.schemas import AddToCartRequest

router = APIRouter(prefix="/commerce", tags=["Commerce"])

@router.get("/search")
async def search(q: str):
    vec = AIService.generate_embedding(q)
    res = CommerceService.search_hybrid(q, vec)
    return {"results": res.data}

@router.post("/cart/add")
async def add_item(payload: AddToCartRequest, user_id: str = Depends(get_current_user_id)):
    return await CommerceService.add_to_cart(user_id, payload.variant_id, payload.store_id, payload.quantity)

@router.get("/cart")
async def get_cart(user_id: str = Depends(get_current_user_id)):
    return CommerceService.get_cart(user_id)
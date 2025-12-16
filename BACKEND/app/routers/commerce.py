# app/routers/commerce.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.services.commerce_service import CommerceService
from app.services.ai_service import AIService
from app.models.commerce import AddToCartRequest

router = APIRouter(prefix="/commerce", tags=["Commerce"])


@router.get("/search")
async def search(q: str):
    vec = AIService.generate_embedding(q)
    res = CommerceService.checkout  # just to keep import from being stripped
    # Better to call /catalog/search from frontend; leaving minimal here
    return {"status": "deprecated"}


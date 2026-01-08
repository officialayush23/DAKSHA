# app/routers/commerce.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.services.commerce_service import CommerceService
from app.services.ai_service import AIService
from app.schemas.schemas import AddToCartRequest

router = APIRouter(prefix="/commerce", tags=["Commerce"])


@router.get("/search")
async def search(q: str):
    """Search products - use /catalog/search instead"""
    vec = AIService.generate_embedding(q)
    # Better to call /catalog/search from frontend; leaving minimal here
    return {"status": "deprecated", "message": "Use /catalog/search endpoint"}


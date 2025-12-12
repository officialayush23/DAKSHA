# app/routers/recommendations.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services.recommendation_service import RecommendationService
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/home")
async def home_recommendations(user_id: Optional[str] = Depends(get_current_user_id), limit: int = Query(8, ge=1, le=32)):
    # get_current_user_id raises 401 for unauth; you may wrap it with optional auth for guest use
    items = RecommendationService.get_personalized_recommendations(user_id, limit)
    return {"items": items}


@router.get("/trending")
async def trending(limit: int = Query(8, ge=1, le=32)):
    items = RecommendationService.get_trending_products(limit)
    return {"items": items}

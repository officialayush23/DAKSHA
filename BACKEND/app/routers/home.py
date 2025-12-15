from fastapi import APIRouter, Depends, Query
from app.core.auth_optional import get_optional_user_id
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/home", tags=["Home"])


@router.get("")
async def home(
    limit: int = Query(8, ge=1, le=12),
    user_id: str | None = Depends(get_optional_user_id),
):
    user_context = {
        "user_type": "guest" if not user_id else "logged_in",
        "user_id": user_id,
    }

    items = RecommendationService.for_home(
        user_context=user_context,
        limit=limit,
    )

    return {
        "hero": {
            "title": "Picked just for you",
            "subtitle": "AI-curated products you’ll love",
            "cta": {
                "label": "Start shopping",
                "href": "/products",
            },
        },
        "sections": [
            {
                "id": "trending",
                "title": "Trending now",
                "subtitle": "Popular with customers",
                "items": items,
            }
        ],
    }

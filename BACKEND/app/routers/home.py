# app/routers/home.py


from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user_optional
from app.services.recommendation_service import RecommendationService
from app.services.inventory_service import InventoryService
from app.database import supabase

router = APIRouter(prefix="/home", tags=["Home"])
@router.get("")
async def home(
    limit: int = Query(8, le=12),
    user = Depends(get_current_user_optional),
):
    user_context = {
        "user_type": "guest" if not user else "logged_in",
        "user_id": user["id"] if user else None,
    }

    # 1️⃣ Personalized / fallback
    personalized = RecommendationService.for_home(
        user_context=user_context,
        limit=limit
    )

    # 2️⃣ Location-aware trending
    city = None
    if user:
        addr = (
            supabase.table("user_addresses")
            .select("city")
            .eq("user_id", user["id"])
            .eq("is_default", True)
            .maybe_single()
            .execute()
        ).data
        city = addr["city"] if addr else None

    trending = (
        InventoryService.trending_near_city(city, limit)
        if city else
        RecommendationService.trending_global(limit)
    )

    return {
        "hero": {
            "title": "Picked just for you",
            "subtitle": "AI-curated based on your interests",
            "cta": {
                "label": "Start shopping",
                "href": "/products"
            }
        },
        "sections": [
            {
                "id": "personalized",
                "title": "Picked for you",
                "subtitle": "Personalized by Daksha AI",
                "items": personalized,
            },
            {
                "id": "trending_near_you",
                "title": "Trending near you",
                "subtitle": f"Popular in {city}" if city else "Trending with customers",
                "items": trending,
            },
        ],
    }

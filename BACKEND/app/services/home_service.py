# app/services/home_service.py

from typing import Optional, Dict, Any
from datetime import datetime
from app.database import supabase
from app.services.recommendation_service import RecommendationService
from app.services.inventory_service import InventoryService


class HomeService:

    @staticmethod
    async def build_home(user: Optional[dict]) -> Dict[str, Any]:
        context = HomeService._resolve_context(user)

        hero = HomeService._build_hero(context)

        sections = []

        # Order matters (business-driven)
        sections += HomeService._inventory_section(context)
        sections += HomeService._personalized_section(context)
        sections += HomeService._campaign_section(context)
        sections += HomeService._trending_section(context)

        return {
            "context": context,
            "hero": hero,
            "sections": sections,
        }

    # --------------------------------------------------
    # CONTEXT
    # --------------------------------------------------

    @staticmethod
    def _resolve_context(user: Optional[dict]) -> dict:
        now = datetime.utcnow()
        return {
            "user_type": (
                "guest" if not user else
                "loyal" if user.get("loyalty_tier") else
                "logged_in"
            ),
            "location": {
                "city": user.get("city") if user else None,
                "lat": user.get("latitude") if user else None,
                "lng": user.get("longitude") if user else None,
            },
            "time_context": {
                "hour": now.hour,
                "season": HomeService._season(now.month),
            },
        }

    @staticmethod
    def _season(month: int) -> str:
        if month in (6, 7, 8):
            return "monsoon"
        if month in (11, 12):
            return "festive"
        return "regular"

    # --------------------------------------------------
    # HERO
    # --------------------------------------------------

    @staticmethod
    def _build_hero(context: dict) -> dict:
        return {
            "title": "Find your perfect fit",
            "subtitle": "Personalized by Daksha AI",
            "primary_cta": {
                "label": "Shop with AI",
                "action": "open_agent",
            },
            "secondary_cta": {
                "label": "Browse products",
                "action": "navigate:/products",
            },
        }

    # --------------------------------------------------
    # SECTIONS
    # --------------------------------------------------

    @staticmethod
    def _inventory_section(context: dict) -> list:
        if not context["location"]["city"]:
            return []

        items = InventoryService.trending_near_city(
            city=context["location"]["city"],
            limit=8,
        )

        if not items:
            return []

        return [{
            "id": "near_you",
            "type": "inventory_driven",
            "title": "Trending near you",
            "reason": f"High demand in {context['location']['city']}",
            "items": items,
        }]

    @staticmethod
    def _personalized_section(context: dict) -> list:
        if context["user_type"] == "guest":
            return []

        items = RecommendationService.for_home(
            user_context=context,
            limit=8,
        )

        if not items:
            return []

        return [{
            "id": "personalized",
            "type": "ai_recommendation",
            "title": "Picked for you",
            "reason": "Based on your browsing and purchases",
            "algorithm": "vector_v2",
            "items": items,
        }]

    @staticmethod
    def _campaign_section(context: dict) -> list:
        campaigns = (
            supabase.table("home_campaigns")
            .select("*")
            .eq("is_active", True)
            .order("priority")
            .limit(1)
            .execute()
        ).data or []

        if not campaigns:
            return []

        campaign = campaigns[0]

        return [{
            "id": f"campaign_{campaign['id']}",
            "type": "merchandising",
            "title": campaign["title"],
            "items": campaign["items"],
        }]

    @staticmethod
    def _trending_section(context: dict) -> list:
        items = RecommendationService.trending_global(limit=8)

        return [{
            "id": "trending_global",
            "type": "behavioral",
            "title": "Trending now",
            "items": items,
        }]

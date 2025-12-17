#   app/services/home_service.py

from typing import Optional
from app.services.recommendation_service import RecommendationService
from app.services.promotion_service import PromotionService
from app.database import supabase
import logging

logger = logging.getLogger("daksha.home")


class HomeService:

    @staticmethod
    def get_home(user_id: Optional[str]):
        hero = {
            "title": "Smart picks for you",
            "subtitle": "Trending styles, ready to ship",
            "cta": {"label": "Explore", "href": "/products"},
        }

        sections = []

        try:
            # -------------------------------------------------
            # OFFERS (SAFE)
            # -------------------------------------------------
            try:
                offers = PromotionService.get_active_promotions()
                if offers:
                    sections.append({
                        "id": "offers",
                        "type": "offer_rail",
                        "title": "Limited-time offers",
                        "items": offers[:6],
                    })
            except Exception:
                logger.exception("Offers failed")

            # -------------------------------------------------
            # AI RECOMMENDED
            # -------------------------------------------------
            try:
                ai_items = RecommendationService.get_personalized_recommendations(
                    user_id=user_id,
                    limit=8,
                )
                if ai_items:
                    sections.append({
                        "id": "recommended",
                        "type": "product_rail",
                        "title": "Recommended for you",
                        "subtitle": "Picked by Daksha AI",
                        "ai_reason": "Based on your browsing",
                        "items": ai_items,
                    })
            except Exception:
                logger.exception("AI recommendations failed")

            # -------------------------------------------------
            # TRENDING (LAST SAFE FALLBACK)
            # -------------------------------------------------
            try:
                trending = RecommendationService.for_home({}, limit=8)
                if trending:
                    sections.append({
                        "id": "trending",
                        "type": "product_rail",
                        "title": "Trending now",
                        "subtitle": "Popular with customers",
                        "items": trending,
                    })
            except Exception:
                logger.exception("Trending failed")

            # -------------------------------------------------
            # GENDER RAILS (SAFE)
            # -------------------------------------------------
            for gender in ["men", "women", "unisex", "kids"]:
                try:
                    rows = (
                        supabase.table("products")
                        .select("""
                            id,
                            name,
                            gender,
                            base_price,
                            product_variants (
                                id,
                                image_url,
                                inventory (
                                    quantity_on_hand
                                )
                            )
                        """)
                        .eq("gender", gender)
                        .eq("is_active", True)
                        .limit(8)
                        .execute()
                    ).data or []

                    items = []

                    for p in rows:
                        for v in p.get("product_variants") or []:
                            inv_rows = v.get("inventory") or []
                            qty = sum(i.get("quantity_on_hand", 0) for i in inv_rows)
                            if qty > 0:
                                items.append({
                                    "id": p["id"],
                                    "name": p["name"],
                                    "gender": p["gender"],
                                    "image_url": v.get("image_url"),
                                    "price": p["base_price"],
                                    "rating": None,
                                    "review_count": 0,
                                    "badge": None,
                                    "agent_reason": f"Top picks for {gender}",
                                    "inventory": {
                                        "available": True,
                                        "quantity": qty,
                                    },
                                })
                                break

                    if items:
                        sections.append({
                            "id": gender,
                            "type": "product_rail",
                            "title": gender.capitalize(),
                            "subtitle": f"Top picks for {gender}",
                            "items": items,
                        })

                except Exception:
                    logger.exception("Gender rail failed: %s", gender)

        except Exception:
            logger.exception("Home feed hard failure")

        # 🔒 ABSOLUTE GUARANTEE
        return {
            "hero": hero,
            "sections": sections,
        }

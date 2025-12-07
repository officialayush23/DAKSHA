from app.database import supabase
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService


class RecommendationService:
    @staticmethod
    def get_personalized_recommendations(user_id: str, limit: int = 5):
        footprints = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .order("captured_at", desc=True)
            .limit(10)
            .execute()
        )

        if not footprints.data:
            return CatalogService.search_products(
                "bestsellers", AIService.generate_embedding("popular"), limit
            )

        context_text = "User history: " + ", ".join(
            [str(f["event_data"]) for f in footprints.data]
        )

        user_vector = AIService.generate_embedding(context_text)

        return CatalogService.search_products("personalized", user_vector, limit)

    @staticmethod
    def get_active_campaigns(user_id: str):
        res = (
            supabase.table("ad_campaigns")
            .select("*")
            .eq("is_active", True)
            .execute()
        )
        return res.data

from app.database import supabase
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService

class RecommendationService:
    @staticmethod
    def get_personalized_recommendations(user_id: str, limit: int = 5):
        """
        1. Reads user footprints (history).
        2. Generates a 'User Vibe' embedding.
        3. Searches catalog for matching items.
        """
        # 1. Fetch last 10 interactions
        footprints = supabase.table("user_footprints")\
            .select("event_data")\
            .eq("user_id", user_id)\
            .order("captured_at", desc=True)\
            .limit(10)\
            .execute()
        
        if not footprints.data:
            # Cold Start: Return trending items (simplified)
            return CatalogService.search_products("bestsellers", AIService.generate_embedding("popular"), limit)

        # 2. Construct Context String
        # e.g. "Viewed Red Shirt, Added Blue Jeans to Cart, Viewed Summer Dress"
        context_text = "User history: " + ", ".join(
            [str(f['event_data']) for f in footprints.data]
        )

        # 3. Generate "Vibe" Embedding
        user_vector = AIService.generate_embedding(context_text)

        # 4. Search Catalog
        return CatalogService.search_products("personalized", user_vector, limit)

    @staticmethod
    def get_active_campaigns(user_id: str):
        """Returns ads relevant to the user."""
        # Simple logic: Fetch active campaigns. 
        # In prod, filter by user gender/preferences.
        res = supabase.table("ad_campaigns").select("*").eq("is_active", True).execute()
        return res.data
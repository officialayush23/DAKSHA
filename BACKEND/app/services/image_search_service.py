# app/services/image_search_service.py

from app.services.ai_service import AIService
from app.core.database import supabase

class ImageSearchService:
    @staticmethod
    def find_similar_products(user_image_embedding, limit=5):
        return (
            supabase.rpc(
                "match_product_variants",
                {
                    "query_embedding": user_image_embedding,
                    "match_count": limit,
                },
            )
            .execute()
            .data
        )

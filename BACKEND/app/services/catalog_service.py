# app/services/catalog_service.py

from app.core.database import supabase
from typing import List


class CatalogService:

    @staticmethod
    def search_products(query: str, embedding: List[float], limit: int = 10):
        """
        Hybrid search:
        - text search
        - vector similarity
        """

        try:
            res = supabase.rpc(
                "search_products_hybrid",
                {
                    "query_text": query,
                    "query_embedding": embedding,
                    "match_count": limit,
                },
            ).execute()

            return res.data or []
        except Exception:
            # fallback: text-only
            return (
                supabase.table("products")
                .select("*")
                .ilike("name", f"%{query}%")
                .limit(limit)
                .execute()
            ).data

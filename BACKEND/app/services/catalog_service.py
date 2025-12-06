from fastapi import HTTPException
from app.database import supabase


class CatalogService:
    @staticmethod
    def search_products(query: str, embedding: list[float], limit: int = 10):
        res = supabase.rpc(
            "search_products_hybrid",
            {
                "query_text": query,
                "query_embedding": embedding,
                "match_threshold": 0.5,
                "match_count": limit,
            },
        ).execute()
        if res.error:
            raise HTTPException(500, f"Search failed: {res.error.message}")
        return res.data

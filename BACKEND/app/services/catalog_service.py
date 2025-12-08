from fastapi import HTTPException
from app.database import supabase
from postgrest.exceptions import APIError


class CatalogService:
    @staticmethod
    def get_products(category: str = None, brand: str = None, sort: str = "newest"):
        query = supabase.from_("products").select("*")

        if category:
            query = query.eq("category_id", category)

        if brand:
            query = query.eq("brand", brand)

        if sort == "newest":
            query = query.order("created_at", desc=True)
        elif sort == "price_asc":
            query = query.order("price", desc=False)
        elif sort == "price_desc":
            query = query.order("price", desc=True)

        try:
            res = query.execute()
            return res.data
        except APIError as e:
            raise HTTPException(500, f"Failed to fetch products: {e.message}")

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

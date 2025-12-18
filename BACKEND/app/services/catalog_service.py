# app/services/catalog_service.py

from app.database import supabase
from typing import List


class CatalogService:

    @staticmethod
    def search_products(query: str, embedding: list = None, limit: int = 5):
        """
        Robust search: Uses Vector Search if embedding provided, 
        otherwise falls back to Keyword Search (ILIKE) for free text-only mode.
        """
        try:
            # 1. IF Embedding exists -> Vector Search (Better accuracy)
            if embedding:
                print(f"🔍 Searching with Vector Embedding...")
                response = supabase.rpc(
                    "match_products",
                    {
                        "query_embedding": embedding,
                        "match_threshold": 0.5,
                        "match_count": limit
                    }
                ).execute()
                return response.data

            # 2. ELSE -> Text Search (Fallback / Free Tier)
            # Breaks query into keywords: "red shoes" -> "red" & "shoes"
            print(f"🔍 Searching via Text (No Embedding)...")
            keywords = query.replace(" ", "%")
            
            # Simple ILIKE search on name or description
            response = supabase.table("products")\
                .select("id, name, base_price, description, category_id")\
                .or_(f"name.ilike.%{keywords}%,description.ilike.%{keywords}%")\
                .limit(limit)\
                .execute()
                
            return response.data

        except Exception as e:
            print(f"❌ Catalog Search Error: {e}")
            return []

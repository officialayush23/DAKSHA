import json
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.candidate_service import generate_candidates
from app.services.catalog_semantic_service import semantic_catalog_search, search_similar_by_image
from app.services.trending_service import get_trending_feed

@tool
def recommend_products(user_id: str, intent_text: str = None) -> str:
    """Gets personalized product recommendations for the user based on their intent or history."""
    with SessionLocal() as db:
        try:
            candidates = generate_candidates(db, user_id=user_id, intent_text=intent_text, limit=10)
            if not candidates:
                return "No recommendations found right now."
            return json.dumps({"recommended_variant_ids": candidates})
        except Exception as e:
            return f"Action failed: {str(e)}"

@tool
def search_for_items(query: str) -> str:
    """Searches the catalog for specific items using semantic text search (e.g. 'red wedding dress')."""
    with SessionLocal() as db:
        try:
            results = semantic_catalog_search(db, query=query, limit=10)
            return json.dumps({"search_results_variant_ids": results})
        except Exception as e:
            return f"Search failed: {str(e)}"
        
@tool
def find_similar_by_image(image_url: str) -> str:
    """Finds visually similar items in the catalog based on an image URL."""
    with SessionLocal() as db:
        try:
            results = search_similar_by_image(db, image_url=image_url, limit=10)
            return json.dumps({"image_search_variant_ids": results})
        except Exception as e:
            return f"Image search failed: {str(e)}"

@tool
def get_trending_products(user_id: str = None) -> str:
    """Gets the current trending or popular products."""
    with SessionLocal() as db:
        try:
            results = get_trending_feed(db, user_id=user_id, limit=10)
            return json.dumps({"trending_products": results})
        except Exception as e:
            return f"Trending fetch failed: {str(e)}"
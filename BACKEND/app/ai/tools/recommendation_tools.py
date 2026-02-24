# app/ai/tools/recommendation_tools.py
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.candidate_service import generate_candidates
from app.services.catalog_semantic_service import semantic_catalog_search,search_similar_by_image

@tool
def recommend_products(user_id: str, intent_text: str = None) -> str:
    """Gets personalized product recommendations for the user based on their intent or history."""
    with SessionLocal() as db:
        try:
            # We call your enterprise candidate pipeline
            candidates = generate_candidates(db, user_id=user_id, intent_text=intent_text, limit=5)
            if not candidates:
                return "No recommendations found right now."
            return f"Showed these products to user: {candidates}"
        except Exception as e:
            return f"Action failed: {str(e)}"

@tool
def search_for_items(query: str) -> str:
    """Searches the catalog for specific items using semantic search (e.g. 'red wedding dress')."""
    with SessionLocal() as db:
        try:
            results = semantic_catalog_search(db, query=query, limit=5)
            return f"Found these items: {results}"
        except Exception as e:
            return f"Search failed: {str(e)}"
        
        
@tool
def find_similar_by_image(image_url: str) -> str:
    """Finds visually similar items in the catalog based on an image."""
    with SessionLocal() as db:
        try:
            results = search_similar_by_image(db, image_url=image_url, limit=5)
            return f"Found these visually similar items: {results}"
        except Exception as e:
            return f"Image search failed: {str(e)}" 
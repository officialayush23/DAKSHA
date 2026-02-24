# app/ai/tools/recommendation_tools.py
import json
from langchain.tools import tool
from app.core.database import SessionLocal

from app.services.candidate_service import generate_candidates
from app.services.catalog_semantic_service import semantic_catalog_search, search_similar_by_image
from app.services.trending_service import get_trending_feed

# IMPORT MODELS FOR HYDRATION
from app.models.models import ProductVariant, Product, ProductImage
from app.services.pricing_service import resolve_variant_price

def _hydrate_variant_ids(db, variant_ids: list) -> list:
    """Helper to turn raw DB IDs into rich UI objects (name, image, price) for the frontend."""
    if not variant_ids:
        return []
    
    # Fetch all variants
    variants = db.query(ProductVariant).filter(ProductVariant.id.in_(variant_ids)).all()
    variant_dict = {str(v.id): v for v in variants}
    
    hydrated = []
    # Loop over original IDs to maintain the search ranking order!
    for vid in variant_ids:
        v = variant_dict.get(str(vid))
        if not v: 
            continue
            
        p = db.query(Product).get(v.product_id)
        img = db.query(ProductImage).filter_by(product_variant_id=v.id).first()
        
        try:
            price_data = resolve_variant_price(db, v)
            final_price = price_data.get("final_price", v.base_price)
        except:
            final_price = v.base_price

        hydrated.append({
            "variant_id": str(v.id),
            "name": p.name if p else "Product",
            "image": img.image_url if img else "https://via.placeholder.com/200",
            "price": float(final_price) # React looks for p.price or p.final_price
        })
        
    return hydrated


@tool
def recommend_products(user_id: str, intent_text: str = None) -> str:
    """Gets personalized product recommendations for the user based on their intent or history."""
    with SessionLocal() as db:
        try:
            candidates = generate_candidates(db, user_id=user_id, intent_text=intent_text, limit=10)
            products = _hydrate_variant_ids(db, candidates)
            # 👇 WE EXPLICITLY USE THE "products" KEY FOR THE REACT FRONTEND
            return json.dumps({"products": products})
        except Exception as e:
            return f"Action failed: {str(e)}"

@tool
def search_for_items(query: str) -> str:
    """Searches the catalog for specific items using semantic text search (e.g. 'red wedding dress')."""
    with SessionLocal() as db:
        try:
            results = semantic_catalog_search(db, query=query, limit=10)
            products = _hydrate_variant_ids(db, results)
            return json.dumps({"products": products})
        except Exception as e:
            return f"Search failed: {str(e)}"
        
@tool
def find_similar_by_image(image_url: str) -> str:
    """Finds visually similar items in the catalog based on an image URL."""
    with SessionLocal() as db:
        try:
            results = search_similar_by_image(db, image_url=image_url, limit=10)
            products = _hydrate_variant_ids(db, results)
            return json.dumps({"products": products})
        except Exception as e:
            return f"Image search failed: {str(e)}"

@tool
def get_trending_products(user_id: str = None) -> str:
    """Gets the current trending or popular products."""
    with SessionLocal() as db:
        try:
            results = get_trending_feed(db, user_id=user_id, limit=10)
            return json.dumps({"products": results})
        except Exception as e:
            return f"Trending fetch failed: {str(e)}"
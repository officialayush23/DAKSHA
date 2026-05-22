# app/ai/tools/recommendation_tools.py
import json
import uuid
import logging
from langchain.tools import tool
from app.core.database import SessionLocal

from app.services.candidate_service import generate_candidates
from app.services.catalog_semantic_service import semantic_catalog_search, search_similar_by_image
from app.services.trending_service import get_trending_feed

from app.models.models import ProductVariant, Product, ProductImage, RecommendationImpression, GlobalInventory
from app.services.pricing_service import resolve_variant_price
from app.enums.db_enums import RecommendationFeedEnum

logger = logging.getLogger(__name__)


def _hydrate_variant_ids(db, variant_ids: list) -> list:
    """
    Turn raw DB IDs into rich UI objects for the frontend.
    Only returns variants that are:
      - active=True
      - have available stock (total_stock - reserved_stock - assigned_stock > 0)
    Each item includes variant_id, color, size, sku so the agent can
    distinguish between different variants of the same product.
    """
    if not variant_ids:
        return []

    variants = (
        db.query(ProductVariant)
        .filter(ProductVariant.id.in_(variant_ids), ProductVariant.active == True)
        .all()
    )
    variant_dict = {str(v.id): v for v in variants}

    inv_rows = (
        db.query(GlobalInventory)
        .filter(GlobalInventory.variant_id.in_(variant_ids))
        .all()
    )
    inv_dict = {str(row.variant_id): row for row in inv_rows}

    hydrated = []
    for vid in variant_ids:
        v = variant_dict.get(str(vid))
        if not v:
            continue

        inv = inv_dict.get(str(vid))
        if inv:
            available = inv.total_stock - inv.reserved_stock - getattr(inv, "assigned_stock", 0)
            if available <= 0:
                continue

        p = db.query(Product).get(v.product_id)
        img = db.query(ProductImage).filter_by(product_variant_id=v.id).first()

        try:
            price_data = resolve_variant_price(db, v)
            final_price = price_data.get("final_price", v.base_price)
        except Exception:
            final_price = v.base_price

        hydrated.append({
            "variant_id": str(v.id),
            "product_id": str(v.product_id),
            "name": p.name if p else "Product",
            "color": v.color or None,
            "size": v.size or None,
            "sku": v.sku or None,
            "image": img.image_url if img else "https://via.placeholder.com/200",
            "price": float(final_price) if final_price else 0.0,
        })

    return hydrated


def _log_impressions(db, user_id, session_id, products, feed):
    try:
        rows = []
        for rank, item in enumerate(products):
            imp_id = uuid.uuid4()
            item["impression_id"] = str(imp_id)
            rows.append(RecommendationImpression(
                id=imp_id,
                user_id=uuid.UUID(user_id) if user_id else None,
                session_id=uuid.UUID(session_id) if session_id else None,
                product_variant_id=uuid.UUID(item["variant_id"]) if item.get("variant_id") else None,
                feed=feed,
                rank_position=rank + 1,
            ))
        db.add_all(rows)
        db.commit()
    except Exception as e:
        logger.warning(f"Impression log failed: {e}")
    return products


@tool
def recommend_products(user_id: str, session_id: str = None, intent_text: str = None) -> str:
    """Gets personalized product recommendations for the user based on their intent or history."""
    with SessionLocal() as db:
        try:
            candidates = generate_candidates(db, user_id=user_id, intent_text=intent_text, limit=10)
            products = _hydrate_variant_ids(db, candidates)
            products = _log_impressions(db, user_id, session_id, products, RecommendationFeedEnum.home)
            return json.dumps({"products": products})
        except Exception as e:
            return f"Action failed: {str(e)}"


@tool
def search_for_items(query: str, user_id: str = None, session_id: str = None) -> str:
    """Searches the catalog for specific items using semantic text search."""
    with SessionLocal() as db:
        try:
            results = semantic_catalog_search(db, query=query, limit=10)
            products = _hydrate_variant_ids(db, results)
            products = _log_impressions(db, user_id, session_id, products, RecommendationFeedEnum.search)
            return json.dumps({"products": products})
        except Exception as e:
            return f"Search failed: {str(e)}"


@tool
def find_similar_by_image(image_url: str, user_id: str = None, session_id: str = None) -> str:
    """Finds visually similar items in the catalog based on an image URL."""
    with SessionLocal() as db:
        try:
            results = search_similar_by_image(db, image_url=image_url, limit=10)
            products = _hydrate_variant_ids(db, results)
            products = _log_impressions(db, user_id, session_id, products, RecommendationFeedEnum.image_search)
            return json.dumps({"products": products})
        except Exception as e:
            return f"Image search failed: {str(e)}"


@tool
def get_trending_products(user_id: str = None, session_id: str = None) -> str:
    """Gets the current trending or popular products."""
    with SessionLocal() as db:
        try:
            results = get_trending_feed(db, user_id=user_id, limit=10)
            results = _log_impressions(db, user_id, session_id, results, RecommendationFeedEnum.trending)
            return json.dumps({"products": results})
        except Exception as e:
            return f"Trending fetch failed: {str(e)}"

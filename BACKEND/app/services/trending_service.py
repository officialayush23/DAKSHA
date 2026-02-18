# app/services/trending_service.py
from app.models.models import ProductVariant
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.impression_service import log_impressions
from app.services.pricing_service import resolve_variant_price

def get_trending_feed(db: Session, user_id: str = None, limit: int = 20):
    """
    Returns the 'Cold Start' feed based on the materialized trending_products table.
    """
    # Fetch pre-computed trends
    query = text("""
        SELECT 
            pv.id as variant_id, pv.base_price as price, 
            p.name, p.brand, p.category, 
            pi.image_url,
            tp.trending_score
        FROM trending_products tp
        JOIN product_variants pv ON tp.product_variant_id = pv.id
        JOIN products p ON pv.product_id = p.id
        LEFT JOIN product_images pi ON pi.product_variant_id = pv.id AND pi.position = 1
        WHERE tp.scope = 'global'
        ORDER BY tp.rank_position ASC
        LIMIT :limit
    """)
    
    results = db.execute(query, {"limit": limit}).fetchall()
    items = [dict(row._mapping) for row in results]
    
    hydrated = []
    for row in results:
        variant = db.query(ProductVariant).get(row.variant_id)
        
        if not variant:
            continue

        price = resolve_variant_price(db, variant)

        hydrated.append({
            "variant_id": variant.id,
            "product_id": variant.product_id,
            "name": row.name,
            "brand": row.brand,
            "category": row.category,
            "image": row.image_url,
            "base_price": price["base_price"],
            "final_price": price["final_price"],
            "offer_name": price["offer_name"],
            "score": float(row.trending_score),
            "reason": "trending",
        })

    items = hydrated



    # Log Impression
    if user_id:
        log_impressions(db, user_id, items, feed_type="trending")

    return items
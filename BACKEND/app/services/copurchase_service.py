# app/services/copurchase_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from app.services.offer_service import attach_offers_to_products
from app.services.impression_service import log_impressions

def get_bought_together(
    db: Session,
    variant_id: str,
    user_id: str = None,
    session_id: str = None,
    limit: int = 5,
):
    """
    Efficient Graph Lookup for PDP.
    Uses 'product_affinities' table built by ML background job.
    """
    # 1. Query Graph Table
    query = text("""
        SELECT 
            pv.id as variant_id, pv.base_price as price,
            p.name, p.brand, p.category,
            pi.image_url,
            pa.score
        FROM product_affinities pa
        JOIN product_variants pv ON pa.product_variant_id_b = pv.id
        JOIN products p ON pv.product_id = p.id
        LEFT JOIN product_images pi ON pi.product_variant_id = pv.id AND pi.position = 1
        WHERE pa.product_variant_id_a = :vid
          AND pa.context_scope = 'global'
        ORDER BY pa.score DESC
        LIMIT :limit
    """)
    
    rows = db.execute(query, {"vid": variant_id, "limit": limit}).fetchall()
    items = [dict(row._mapping) for row in rows]

    # 2. Attach Pricing
    items = attach_offers_to_products(db, items)

    # 3. Log
    if user_id:
        log_impressions(db, user_id, items, feed_type="bought_together", session_id=session_id)

    return items
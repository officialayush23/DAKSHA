# app/services/ranking_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from sqlalchemy import or_
from app.services.embedding_service import generate_text_embedding
from app.services.pricing_service import resolve_variant_price
from app.models.models import ProductDiscountRule
def rank_candidates(
    db: Session,
    user_id: str,
    candidate_ids: list,
    intent_text: str = None,
    limit: int = 100
):
    """
    Phase 2: RANK
    Scores recalled candidates using content similarity,
    intent relevance, and trending signals.
    """

    if not candidate_ids:
        return []

    # ✅ compute embedding once
    intent_vec = (
    str(generate_text_embedding(intent_text))
    if intent_text
    else None
)

    sql = text("""
    WITH user_pref AS (
        SELECT COALESCE(
            (SELECT embedding FROM user_preference_summary WHERE user_id = :uid),
            array_fill(0, ARRAY[768])::vector
        ) AS vec
    )
    SELECT 
        pv.id AS variant_id,
        p.id AS product_id,
        p.brand,
        p.category,
        p.name,
        pv.base_price,
        pi.image_url,

        -- content similarity
        (1 - (pe.embedding <=> (SELECT vec FROM user_pref))) AS content_score,

        -- intent similarity (safe null handling)
        CASE 
            WHEN :intent_vec IS NULL THEN 0
            ELSE (1 - (pe.embedding <=> CAST(:intent_vec AS vector)))
        END AS intent_score,

        -- trending boost
        COALESCE((
            SELECT 1.0 / rank_position
            FROM trending_products
            WHERE product_variant_id = pv.id
              AND scope='global'
            LIMIT 1
        ), 0) AS trend_score

    FROM product_variants pv
    JOIN products p ON pv.product_id = p.id
    LEFT JOIN product_multimodal_embeddings pe 
        ON pe.product_variant_id = pv.id
        AND pe.modality = 'text'
    LEFT JOIN product_images pi 
        ON pi.product_variant_id = pv.id
        AND pi.position = 1

    WHERE pv.id::text = ANY(:candidates)
      AND p.active = true
      AND pv.active = true
    """)

    rows = db.execute(sql, {
        "uid": user_id,
        "intent_vec": intent_vec,
        "candidates": candidate_ids,
    }).fetchall()

    # dynamic weights
    w_intent, w_content, w_trend = (
        (0.6, 0.2, 0.2) if intent_text else (0.0, 0.6, 0.4)
    )

    results = []
    
    now = datetime.utcnow()

    rules = db.query(ProductDiscountRule).filter(
        ProductDiscountRule.active.is_(True),
        ProductDiscountRule.valid_from <= now,
        or_(
            ProductDiscountRule.valid_to.is_(None),
            ProductDiscountRule.valid_to >= now
        )
    ).all()

    for r in rows:
        final_score = (
            w_intent * (r.intent_score or 0) +
            w_content * (r.content_score or 0) +
            w_trend * (r.trend_score or 0)
        )

        price_data = resolve_variant_price(
            db=db,
            variant_id=r.variant_id,
            base_price=r.base_price,
            category=r.category,
            brand=r.brand,
            rules_cache=rules
        )

        results.append({
            "variant_id": r.variant_id,
            "product_id": r.product_id,
            "name": r.name,
            "brand": r.brand,
            "category": r.category,
            "image": r.image_url,
            "base_price": price_data["base_price"],
            "final_price": price_data["final_price"],
            "offer_name": price_data.get("offer_name"),
            "scores": {
                "content": r.content_score or 0,
                "intent": r.intent_score or 0,
                "trend": r.trend_score or 0,
            },
            "final_score": final_score,
        })
    return sorted(results, key=lambda x: x["final_score"], reverse=True)[:limit]
# app/services/recommendation_service.py
from sqlalchemy.orm import Session
from app.services.candidate_service import generate_candidates
from app.services.ranking_service import rank_candidates
from app.services.postrank_service import apply_business_rules
from app.services.impression_service import log_impressions
from app.services.offer_service import attach_offers_to_products


from sqlalchemy import func
from app.models.models import (
    ProductVariant,
    Product,
    ProductEmbedding,
    OrderItem,
)
from app.services.pricing_service import resolve_variant_price
from app.services.impression_service import log_impressions

def get_hybrid_recommendations(db: Session, user_id: str, intent_text: str = None, limit: int = 20):
    
    # 1. Candidate Generation (Recall) - Get ~500 items
    candidate_ids = generate_candidates(db, user_id, intent_text, limit=200)

    # 2. Ranking (Precision) - Score them
    ranked_raw = rank_candidates(db, user_id, candidate_ids, intent_text, limit=100)

    # 3. Post-Ranking (Business Logic) - Filter them
    final_feed = apply_business_rules(ranked_raw)

    # Trim to requested limit
    final_feed = final_feed[:limit]

    # 4. Logging (Data Flywheel)
    # Log what we are about to show so we can learn later
    log_impressions(db, user_id, final_feed, feed_type="home_feed" if not intent_text else "search")
    
    
    attach_offers_to_products(db, final_feed)

    # 5. Format for API
    return [
        {
            "product_id": row.id,
            "brand": row.brand,
            "category": row.category,
            "variant_id": row.variant_id,
            "price": row.base_price,
            "image": row.image_url,
            "scores": {
                "content": row.content_score,
                "intent": row.intent_score,
                "trend": row.trend_score
            }
        }
        for row in final_feed
    ]
    
    
    



PRICE_BAND_PERCENT = 0.2
SIMILARITY_LIMIT = 20

def get_similar_variants(
    db: Session,
    base_variant_id,
    user_id=None,
    session_id=None,
    limit=20,
):
    base = (
        db.query(ProductVariant)
        .join(Product)
        .filter(ProductVariant.id == base_variant_id)
        .first()
    )
    if not base:
        return []

    base_emb = (
        db.query(ProductEmbedding)
        .filter(ProductEmbedding.product_variant_id == base_variant_id)
        .first()
    )

    results = []

    if base_emb:
        q = (
            db.query(
                ProductVariant,
                func.cosine_distance(
                    ProductEmbedding.embedding,
                    base_emb.embedding,
                ).label("distance"),
            )
            .join(Product)
            .join(ProductEmbedding)
            .filter(
                ProductVariant.id != base_variant_id,
                Product.category == base.product.category,
                Product.gender == base.product.gender,
                ProductVariant.active.is_(True),
            )
        )

        low = base.base_price * 0.8
        high = base.base_price * 1.2
        q = q.filter(ProductVariant.base_price.between(low, high))

        results = q.order_by("distance").limit(limit).all()

    # 🔁 HARD FALLBACK (category + gender + price)
    if len(results) < limit:
        fallback = (
            db.query(ProductVariant)
            .join(Product)
            .filter(
                ProductVariant.id != base_variant_id,
                Product.category == base.product.category,
                Product.gender == base.product.gender,
                ProductVariant.active.is_(True),
            )
            .limit(limit)
            .all()
        )
        results = [(v, None) for v in fallback]

    out = []
    for rank, (variant, _) in enumerate(results):
        price = resolve_variant_price(db, variant)
        out.append({
            "variant_id": variant.id,
            "product_id": variant.product_id,
            **price,
            "reason": "similar",
            "rank": rank,
        })

    log_impressions(db, user_id, out, "similar", session_id)
    return out

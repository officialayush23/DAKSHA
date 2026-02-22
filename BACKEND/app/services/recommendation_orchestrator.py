# app/services/recommendation_orchestrator.py
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.recommendation_service import get_hybrid_recommendations
from app.services.ranking_service import rank_candidates
from app.services.postrank_service import apply_business_rules
from app.services.impression_service import log_impressions


def get_recommended_feed(
    db: Session,
    *,
    user_id: UUID,
    session_id: UUID,
    intent_text: str | None,
    feed_type: str = "home",
    limit: int = 20,
):
    """
    ENTERPRISE RECOMMENDATION PIPELINE
    """

    # 1️⃣ RECALL
    candidate_ids = get_hybrid_recommendations(
        db,
        str(user_id),
        intent_text,
        limit=300,
    )

    if not candidate_ids:
        return []

    # 2️⃣ RANK
    ranked = rank_candidates(
        db,
        str(user_id),
        candidate_ids,
        intent_text,
        limit=100,
    )

    if not ranked:
        return []

    # 3️⃣ BUSINESS RULES
    diversified = apply_business_rules(ranked)

    # 4️⃣ FORMAT
    final = []
    for r in diversified[:limit]:
        final.append({
            "variant_id": r.variant_id,
            "product_id": r.id,
            "brand": r.brand,
            "category": r.category,
            "price": float(r.base_price),
            "image": r.image_url,
            "reason": "recommended",
        })

    # 5️⃣ IMPRESSION LOGGING
    log_impressions(
        db=db,
        user_id=user_id,
        results=final,
        feed=feed_type,
        session_id=session_id,
    )

    return final

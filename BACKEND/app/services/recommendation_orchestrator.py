# app/services/recommendation_orchestrator.py
# from sqlalchemy.orm import Session
# from typing import Optional, List
# from uuid import UUID

# from app.services.recommendation_service import get_hybrid_recommendations
# from app.services.ranking_service import rank_candidates
# from app.services.post_rank_service import apply_business_rules
# from app.services.personalized_offer_service import get_active_personal_offers
# from app.services.impression_service import log_impressions

# from app.models.models import (
#     ProductVariant,
#     ProductReviewStats,
#     UserPreferenceSummary,
#     UserBehaviorAggregate,
#     StoreInventory,
# )

# PRICE_BAND_TOLERANCE = 0.3   # ±30%
# MIN_REVIEWS = 5


# def get_recommended_feed(
#     db: Session,
#     *,
#     user_id: UUID,
#     session_id: UUID,
#     intent_text: Optional[str],
#     feed_type: str = "home",
#     limit: int = 20,
# ):
#     """
#     CANONICAL RECOMMENDATION ENTRY POINT
#     This is what LangGraph / frontend / agents must call.
#     """

#     # --------------------------------------------------
#     # 1. RECALL (Wide)
#     # --------------------------------------------------
#     recall_items = get_hybrid_recommendations(
#         db=db,
#         user_id=str(user_id),
#         intent_text=intent_text,
#         session_id=session_id,
#         limit=300,     # wide recall
#     )

#     if not recall_items:
#         return []

#     candidate_ids = [str(i["variant_id"]) for i in recall_items]

#     # --------------------------------------------------
#     # 2. RANK (Smart)
#     # --------------------------------------------------
#     ranked = rank_candidates(
#         db=db,
#         user_id=str(user_id),
#         candidate_ids=candidate_ids,
#         intent_text=intent_text,
#         limit=100,
#     )

#     if not ranked:
#         return []

#     # --------------------------------------------------
#     # 3. FILTER (Hard constraints)
#     # --------------------------------------------------
#     prefs = db.query(UserPreferenceSummary).filter_by(user_id=user_id).first()
#     behavior = db.query(UserBehaviorAggregate).get(user_id)

#     min_price = max_price = None
#     if behavior and behavior.avg_viewed_price:
#         min_price = behavior.avg_viewed_price * (1 - PRICE_BAND_TOLERANCE)
#         max_price = behavior.avg_viewed_price * (1 + PRICE_BAND_TOLERANCE)

#     filtered = []
#     for r in ranked:
#         # Price band filter
#         if min_price and not (min_price <= r.base_price <= max_price):
#             continue

#         # Rating filter
#         stats = db.query(ProductReviewStats).get(r.id)
#         if stats and stats.review_count >= MIN_REVIEWS:
#             if prefs and prefs.min_acceptable_rating:
#                 if stats.avg_rating < prefs.min_acceptable_rating:
#                     continue

#         # Inventory check (simple)
#         in_stock = db.query(StoreInventory)\
#             .filter(StoreInventory.product_variant_id == r.variant_id)\
#             .filter(StoreInventory.in_stock > 0)\
#             .count()

#         if in_stock == 0:
#             continue

#         filtered.append(r)

#     # --------------------------------------------------
#     # 4. BUSINESS RULES
#     # --------------------------------------------------
#     diversified = apply_business_rules(filtered)

#     # --------------------------------------------------
#     # 5. FORMAT
#     # --------------------------------------------------
#     final = []
#     for r in diversified[:limit]:
#         final.append({
#             "product_id": r.id,
#             "variant_id": r.variant_id,
#             "brand": r.brand,
#             "category": r.category,
#             "price": float(r.base_price),
#             "image": r.image_url,
#             "reason": "recommended",
#         })

#     # --------------------------------------------------
#     # 6. LOG IMPRESSIONS (MANDATORY)
#     # --------------------------------------------------
#     log_impressions(
#         db=db,
#         user_id=user_id,
#         results=final,
#         feed_type=feed_type,
#         session_id=session_id,
#     )

#     return final

from sqlalchemy.orm import Session
from uuid import UUID

from app.services.recommendation_service import get_hybrid_recommendations
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
    SINGLE CANONICAL RECOMMENDATION ENTRY.
    """

    results = get_hybrid_recommendations(
        db=db,
        user_id=str(user_id),
        intent_text=intent_text,
        session_id=session_id,
        limit=limit,
    )

    if not results:
        return []

    log_impressions(
        db=db,
        user_id=user_id,
        results=results,
        feed_type=feed_type,
        session_id=session_id,
    )

    return results

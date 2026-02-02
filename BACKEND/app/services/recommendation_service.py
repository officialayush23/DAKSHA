# app/services/recommendation_service.py
from sqlalchemy.orm import Session
from app.services.candidate_service import generate_candidates
from app.services.ranking_service import rank_candidates
from app.services.postrank_service import apply_business_rules
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
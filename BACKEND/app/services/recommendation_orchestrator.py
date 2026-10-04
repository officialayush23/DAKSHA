# app/services/recommendation_orchestrator.py
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.recommendation_service import get_hybrid_recommendations
from app.services.ranking_service import rank_candidates
from app.services.postrank_service import apply_business_rules
from app.services.impression_service import log_impressions


def get_recommended_feed(db: Session, *, user_id: UUID, session_id: UUID, intent_text: str | None,
                         feed_type: str = "home", limit: int = 20):
    """Kept for old imports; delegates to the single pipeline."""
    from app.services.recommendation_service import recommend
    return recommend(db, str(user_id), intent_text, limit=limit, session_id=session_id, feed_type=feed_type)

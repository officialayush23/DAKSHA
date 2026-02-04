# app/services/impression_service.py
from sqlalchemy.orm import Session
from app.models.models import RecommendationImpression
import uuid

def log_impressions(
    db: Session,
    user_id,
    results,
    feed_type: str,
    session_id=None,
):
    """
    Canonical impression logger.
    results: list of dicts OR objects with variant_id
    """
    rows = []

    for idx, item in enumerate(results):
        variant_id = (
            item["variant_id"]
            if isinstance(item, dict)
            else item.variant_id
        )

        rows.append(
            RecommendationImpression(
                id=uuid.uuid4(),
                user_id=user_id,
                session_id=session_id,
                product_variant_id=variant_id,
                feed_type=feed_type,
                rank_position=idx + 1,
            )
        )

    db.add_all(rows)
    db.commit()

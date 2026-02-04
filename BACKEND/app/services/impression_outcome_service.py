# app/services/impression_outcome_service.py
import uuid
from sqlalchemy.orm import Session
from app.models.models import RecommendationOutcome

def log_recommendation_outcome(
    db: Session,
    impression_id,
    outcome_type: str,
    reward_value: float = 0.0,
):
    """
    Logs user action taken on a recommendation.
    outcome_type: click | add_to_cart | purchase | wishlist
    """

    db.add(
        RecommendationOutcome(
            id=uuid.uuid4(),
            impression_id=impression_id,
            outcome_type=outcome_type,
            reward_value=reward_value,
        )
    )
    db.commit()

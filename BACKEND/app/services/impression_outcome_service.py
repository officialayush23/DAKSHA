# app/services/impression_outcome_service.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.models import RecommendationOutcome
from datetime import datetime

def log_recommendation_outcome(
    db: Session,
    impression_id: str,
    outcome_type: str,
    reward_value: float = 0.0,
):
    """
    Phase 5: FEEDBACK. Uses PostgreSQL UPSERT. If a user clicks an item, then buys it, 
    we upgrade the reward value for the same impression.
    """
    stmt = insert(RecommendationOutcome).values(
        impression_id=impression_id,
        outcome_type=outcome_type,
        reward=reward_value,
        occurred_at=datetime.utcnow()
    )
    
    stmt = stmt.on_conflict_do_update(
        index_elements=['impression_id'],
        set_={
            'outcome_type': outcome_type, 
            'reward': reward_value, 
            'occurred_at': datetime.utcnow()
        }
    )
    
    db.execute(stmt)
    db.commit()
# app/services/impression_service.py
from sqlalchemy.orm import Session
from app.models.models import RecommendationImpression
import uuid

def log_impressions(db: Session, user_id: str, results, feed_type: str = "home_feed"):
    """
    Async logging of what we showed.
    """
    impressions = []
    for idx, item in enumerate(results):
        imp = RecommendationImpression(
            id=uuid.uuid4(),
            user_id=user_id,
            product_variant_id=item.variant_id,
            feed_type=feed_type,
            rank_position=idx + 1
        )
        impressions.append(imp)
    
    db.add_all(impressions)
    db.commit()
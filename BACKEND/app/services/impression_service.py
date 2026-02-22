# app/services/impression_service.py
from sqlalchemy.orm import Session
from app.models.models import RecommendationImpression
import uuid

def log_impressions(
    db: Session,
    user_id: str,
    results: list,
    feed_type: str,
    session_id: str = None,
):
    """
    Phase 4: LOG. Inserts impressions to DB and INJECTS the `impression_id` 
    into the dictionary payload sent to the frontend.
    """
    rows = []
    clean_user_id = user_id if str(user_id) != "None" else None

    for idx, item in enumerate(results):
        imp_id = uuid.uuid4()
        
        # Inject ID so React can send it back on click!
        item["impression_id"] = str(imp_id)

        rows.append(
            RecommendationImpression(
                id=imp_id,
                user_id=clean_user_id,
                session_id=session_id,
                product_variant_id=item["variant_id"],
                feed=feed_type,
                rank_position=idx + 1,
            )
        )

    db.add_all(rows)
    db.commit()
    return results
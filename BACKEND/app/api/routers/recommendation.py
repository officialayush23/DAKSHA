# app/api/routers/recommendation.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.deps import get_db, get_current_user, get_current_admin

from app.services.candidate_service import generate_candidates
from app.services.ranking_service import rank_candidates
from app.services.postrank_service import apply_business_rules
from app.services.impression_service import log_impressions
from app.services.impression_outcome_service import log_recommendation_outcome
from app.services.trending_service import get_trending_feed
from app.services.copurchase_service import get_bought_together

# For similarity, if you don't have it isolated, you can use hybrid without intent
from app.services.candidate_service import generate_candidates # reused

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/feed")
def get_feed(
    intent: str = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Recall -> Rank -> in-stock filter -> diversify -> log (one shared pipeline)."""
    from app.services.recommendation_service import recommend
    return recommend(db, str(user.id), intent, limit=50, feed_type="search" if intent else "home")


@router.get("/trending")
def get_trending(
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    return get_trending_feed(db, str(user.id), limit=10)

@router.get("/bought-together/{variant_id}")
def bought_together(
    variant_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_bought_together(db, variant_id, str(user.id), limit=10)


class OutcomePayload(BaseModel):
    impression_id: str
    outcome_type: str 
    reward_value: float = 0.1 

@router.post("/outcome")
def record_outcome(payload: OutcomePayload, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """The Feedback Loop - Called by React onClick"""
    log_recommendation_outcome(
        db=db, 
        impression_id=payload.impression_id, 
        outcome_type=payload.outcome_type, 
        reward_value=payload.reward_value
    )
    return {"status": "logged"}


@router.post("/train-model")
def trigger_training(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Consumes Events + Outcomes to train TwoTower Model"""
    from app.services.ml_service import train_collaborative_model  # lazy — torch optional
    background_tasks.add_task(train_collaborative_model, db)
    return {"status": "Training started"}



@router.get("/similar/{variant_id}")
def similar_variants(
    variant_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Similar variants using hybrid recall.
    Returns [] if nothing relevant.
    """

    # reuse hybrid recall WITHOUT intent
    candidate_ids = generate_candidates(
    db,
    str(user.id),
    None,
    limit=100,
    seed_variant_id=variant_id
)

    if not candidate_ids:
        return []

    ranked = rank_candidates(
    db,
    str(user.id),
    candidate_ids,
    intent_text=None,
    limit=20
)

    final = apply_business_rules(ranked)[:10]

    final = log_impressions(
        db,
        str(user.id),
        final,
        feed_type="similar"
    )

    return final
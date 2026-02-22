# app/api/routers/recommendation.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.deps import get_db, get_current_user

from app.services.candidate_service import generate_candidates
from app.services.ranking_service import rank_candidates
from app.services.postrank_service import apply_business_rules
from app.services.impression_service import log_impressions
from app.services.impression_outcome_service import log_recommendation_outcome
from app.services.ml_service import train_collaborative_model
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
    """The Engine: Recall -> Rank -> Filter -> Log"""
    # 1. Recall
    candidate_ids = generate_candidates(db, str(user.id), intent, limit=300)
    
    # 2. Rank
    ranked_raw = rank_candidates(db, str(user.id), candidate_ids, intent, limit=100)
    
    # 3. Post-Rank
    final_feed = apply_business_rules(ranked_raw)[:50] 

    # 4. Log & Inject Impression IDs
    final_feed = final_feed = log_impressions(
    db,
    str(user.id),
    final_feed,
    feed_type="search" if intent else "home"
)

    return final_feed

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
def record_outcome(payload: OutcomePayload, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """Consumes Events + Outcomes to train TwoTower Model"""
    background_tasks.add_task(train_collaborative_model, db)
    return {"status": "Training started"}
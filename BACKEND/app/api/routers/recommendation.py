# app/api/routers/recommendation.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.services.candidate_service import generate_candidates
from app.services.ranking_service import rank_candidates
from app.services.postrank_service import apply_business_rules
from app.services.impression_service import log_impressions
from app.services.ml_service import train_collaborative_model

router = APIRouter(tags=["Discovery"])

@router.get("/feed")
def get_feed(
    intent: str = None, 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    # 1. Recall
    candidate_ids = generate_candidates(db, str(user.id), intent, limit=300)
    
    # 2. Rank
    ranked_raw = rank_candidates(db, str(user.id), candidate_ids, intent, limit=100)
    
    # 3. Post-Rank
    final_feed = apply_business_rules(ranked_raw)
    final_feed = final_feed[:50] # Final Page Size

    # 4. Log (Background)
    # Note: In synchronous FastAPI, this blocks slightly. 
    # For pure async, use BackgroundTasks, but we need DB session there. 
    # Keeping it simple for now.
    log_impressions(db, str(user.id), final_feed, feed_type="search" if intent else "home")

    return [
        {
            "product_id": row.id,
            "brand": row.brand,
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

@router.post("/train-model")
def trigger_training(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    background_tasks.add_task(train_collaborative_model, db)
    return {"status": "Training started"}


from app.services.recommendation_service import get_similar_variants
from app.services.copurchase_service import get_bought_together

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/similar/{variant_id}")
def similar(
    variant_id,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_similar_variants(db, variant_id, user.id, None)


@router.get("/bought-together/{variant_id}")
def bought_together(
    variant_id,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_bought_together(db, variant_id, user.id, None)
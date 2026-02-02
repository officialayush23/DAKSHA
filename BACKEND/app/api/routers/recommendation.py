# app/api/routers/recommendation.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.services.recommendation_service import get_hybrid_recommendations
from app.services.ml_service import train_collaborative_model

router = APIRouter(tags=["Discovery"])

@router.get("/feed")
def get_feed(
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    """
    The main Home Feed. 
    Uses TensorFlow for Collab Filtering + Gemini Vectors for Content.
    """
    return get_hybrid_recommendations(db, str(user.id))

@router.post("/train-model")
def trigger_training(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # In prod, restrict this to Admin only
):
    """
    Triggers the TensorFlow training loop in the background.
    """
    background_tasks.add_task(train_collaborative_model, db)
    return {"status": "Training started in background"}
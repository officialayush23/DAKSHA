# app/api/routers/user_preferences.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, BackgroundTasks
from uuid import UUID

from app.core.deps import get_current_user
from app.core.database import SessionLocal # ⬅️ Import your session maker (adjust path if needed)
from app.services.user_preference_service import build_user_preference_summary

router = APIRouter(prefix="/preferences", tags=["Preferences"])

# Wrapper to ensure the background task gets a dedicated DB session
def run_ai_preference_task(user_id: str):
    db = SessionLocal()
    try:
        build_user_preference_summary(db, user_id)
    finally:
        db.close()

@router.post("/refresh")
def refresh_preferences(
    background_tasks: BackgroundTasks, # ⬅️ Native FastAPI Background processing
    user=Depends(get_current_user)
):
    prefs = getattr(user, "preferences", None)

    # Cleanly handle timezone comparisons
    last_refresh = prefs.last_preference_refresh if prefs else None
    if last_refresh and last_refresh.tzinfo is None:
        last_refresh = last_refresh.replace(tzinfo=timezone.utc)

    should_refresh = (
        prefs is None
        or last_refresh is None
        or last_refresh < datetime.now(timezone.utc) - timedelta(hours=24)
    )

    if should_refresh:
        # Replaces Celery completely. Runs the AI in the background.
        background_tasks.add_task(run_ai_preference_task, str(user.id))
        return {"status": "processing"}

    return {"status": "fresh"}
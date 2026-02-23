# app/api/routers/user_preferences.py
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from uuid import UUID
from app.worker.tasks import refresh_user_preferences
from app.core.deps import get_current_user

router = APIRouter(prefix="/preferences", tags=["Preferences"])

@router.post("/refresh")
def refresh_preferences(user=Depends(get_current_user)):
    prefs = getattr(user, "preferences", None)

    should_refresh = (
        prefs is None
        or prefs.last_preference_refresh is None
        or prefs.last_preference_refresh < datetime.utcnow() - timedelta(hours=24)
    )

    if should_refresh:
        refresh_user_preferences.delay(str(user.id))
        return {"status": "queued"}

    return {"status": "fresh"}
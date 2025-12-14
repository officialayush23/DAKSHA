# # app/routers/analytics.py

from fastapi import APIRouter, BackgroundTasks, Depends
from typing import List, Optional
from app.models.analytics import FootprintCreate
from app.services.analytics_service import AnalyticsService
from app.core.auth_optional import get_optional_user_id

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# --- SINGLE EVENT ---
@router.post("/track")
async def track_event(payload: FootprintCreate,
                      background: BackgroundTasks,
                      user_id: Optional[str] = Depends(get_optional_user_id)):
    
    background.add_task(
        AnalyticsService.log_footprint,
        user_id=user_id, 
        event_type=payload.event_type,
        event_data=payload.event_data,
        session_id=payload.session_id
    )
    return {"status": "queued"}


# --- BULK EVENTS ---
@router.post("/track/bulk")
async def track_events_bulk(events: List[FootprintCreate],
                            background: BackgroundTasks,
                            user_id: Optional[str] = Depends(get_optional_user_id)):

    for ev in events:
        background.add_task(
            AnalyticsService.log_footprint,
            user_id=user_id,
            event_type=ev.event_type,
            event_data=ev.event_data,
            session_id=ev.session_id
        )
    return {"status": f"queued {len(events)} events"}

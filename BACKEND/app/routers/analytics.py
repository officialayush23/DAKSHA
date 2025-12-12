# app/routers/analytics.py
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class FootprintCreate(BaseModel):
    event_type: str
    event_data: Dict[str, Any]
    session_id: Optional[str] = None
    user_id_override: Optional[str] = None


@router.post("/track")
async def track_event(payload: FootprintCreate, background_tasks: BackgroundTasks):
    """
    Lightweight ingestion. Prefer token-based auth in production.
    Frontend should send session_id for guests.
    """
    user_id = payload.user_id_override
    background_tasks.add_task(
        AnalyticsService.log_footprint,
        user_id,
        payload.event_type,
        payload.event_data,
        payload.session_id,
    )
    return {"status": "queued"}

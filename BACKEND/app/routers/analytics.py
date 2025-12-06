from fastapi import APIRouter, BackgroundTasks
from app.models.analytics import FootprintCreate
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _log_footprint(payload: FootprintCreate):
    AnalyticsService.log_footprint(payload.dict())


@router.post("/track")
async def track_event(payload: FootprintCreate, bg: BackgroundTasks):
    bg.add_task(_log_footprint, payload)
    return {"status": "queued"}

# # app/routers/analytics.py
# from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
# from pydantic import BaseModel, Field, root_validator
# from typing import Optional, Any, Dict, List
# from app.services.analytics_service import AnalyticsService
# from app.core.auth import get_current_user_id

# router = APIRouter(prefix="/analytics", tags=["Analytics"])


# class FootprintIn(BaseModel):
#     event_type: str = Field(..., example="view_product")
#     event_data: Dict[str, Any] = Field(default_factory=dict)
#     session_id: Optional[str] = None
#     user_id_override: Optional[str] = None
#     captured_at: Optional[str] = None

#     @root_validator(pre=True)
#     def ensure_event_type(cls, values):
#         if "event_type" not in values or not values["event_type"]:
#             raise ValueError("event_type is required")
#         return values


# class BulkFootprintsIn(BaseModel):
#     events: List[FootprintIn] = Field(..., min_items=1)


# @router.post("/track", status_code=200)
# async def track_event(payload: FootprintIn):
#     """
#     Single event ingestion (already present in your API). Keep for compatibility.
#     """
#     try:
#         AnalyticsService.log_footprint(
#             user_id=payload.user_id_override,
#             event_type=payload.event_type,
#             event_data=payload.event_data,
#             session_id=payload.session_id,
#             captured_at=payload.captured_at,
#         )
#         return {"status": "ok"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/track/bulk", status_code=200)
# async def track_events_bulk(payload: BulkFootprintsIn):
#     """
#     Bulk ingestion. Validates the list and inserts in a single DB operation.
#     """
#     try:
#         # Convert models -> plain dicts for DB insertion
#         records = []
#         for ev in payload.events:
#             rec = {
#                 "event_type": ev.event_type,
#                 "event_data": ev.event_data,
#                 "session_id": ev.session_id,
#                 "user_id": ev.user_id_override,
#                 "captured_at": ev.captured_at,
#             }
#             records.append(rec)

#         inserted = AnalyticsService.log_footprints_bulk(records)
#         return {"status": "ok", "inserted": inserted}
#     except Exception as e:
#         # for bulk, return 400 or 500 as appropriate
#         raise HTTPException(status_code=500, detail=str(e))


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

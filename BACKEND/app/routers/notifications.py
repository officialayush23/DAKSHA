from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.notifications import NotificationCreate
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/")
async def create_notification(payload: NotificationCreate, user_id: str = Depends(get_current_user_id)):
    return await NotificationService.send_to_user(
        payload.user_id, payload.title, payload.body, payload.type or "info"
    )

# app/api/routers/notification.py
# app/api/routers/notifications.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.core.deps import get_db, get_current_user
from app.models.models import OutboundMessage
from app.enums.db_enums import DeliveryChannelEnum
from app.schemas.schemas import NotificationResponse

router = APIRouter(prefix="/user/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(limit: int = 50, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Fetches all in-app notifications for the user's bell icon."""
    notifications = (
        db.query(OutboundMessage)
        .filter(
            OutboundMessage.user_id == user.id,
            OutboundMessage.channel == DeliveryChannelEnum.in_app
        )
        .order_by(desc(OutboundMessage.sent_at))
        .limit(limit)
        .all()
    )
    return notifications
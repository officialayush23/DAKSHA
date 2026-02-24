# app/services/in_app_notifications.py
from app.models.models import OutboundMessage
from app.enums.db_enums import DeliveryChannelEnum, OutboundMessageStatusEnum
from datetime import datetime

def send_in_app_notification(db, user_id, message, entity_id=None, message_type=None):
    msg = OutboundMessage(
        user_id=user_id,
        channel=DeliveryChannelEnum.in_app,
        content=message,
        message_type=message_type,
        status=OutboundMessageStatusEnum.sent,
        sent_at=datetime.utcnow(),
    )
    db.add(msg)
    db.commit()
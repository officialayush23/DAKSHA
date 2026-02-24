# app/services/notification_service.py
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.services.email_service import send_email_and_log
from app.services.telegram_notification_service import send_telegram_and_log
from app.models.models import OutboundMessage
from app.enums.db_enums import DeliveryChannelEnum, OutboundMessageStatusEnum, EntityTypeEnum

async def notify_user(
    db: Session,
    user_id: uuid.UUID,
    subject: str,
    message: str,
    message_type: str,
    entity_id: uuid.UUID = None,
    entity_type: EntityTypeEnum = EntityTypeEnum.user_session,
    send_email: bool = True,
    send_telegram: bool = True,
    send_in_app: bool = True,
):
    """Master service to send omnichannel notifications simultaneously."""
    
    # 1. IN-APP UI NOTIFICATION (Frontend Bell Icon)
    if send_in_app:
        in_app_msg = OutboundMessage(
            user_id=user_id,
            channel=DeliveryChannelEnum.in_app,
            content=message,
            message_type=message_type,
            status=OutboundMessageStatusEnum.sent,
            sent_at=datetime.utcnow()
        )
        db.add(in_app_msg)
        db.commit()

    # 2. EMAIL NOTIFICATION
    if send_email:
        # Convert plain text message to simple HTML for email
        html_content = f"""
        <h3>{subject}</h3>
        <p>{message.replace(chr(10), '<br>')}</p>
        """
        send_email_and_log(
            db=db,
            user_id=user_id,
            subject=subject,
            html_content=html_content,
            message_type=message_type,
            entity_id=entity_id,
            entity_type=entity_type
        )

    # 3. TELEGRAM NOTIFICATION
    if send_telegram:
        await send_telegram_and_log(
            db=db,
            user_id=user_id,
            text=f"*{subject}*\n\n{message}",
            message_type=message_type,
            entity_id=entity_id,
            entity_type=entity_type
        )
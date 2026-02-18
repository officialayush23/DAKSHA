# app/services/telegram_notification_service.py

from sqlalchemy.orm import Session
from app.integrations.telegram_client import send_telegram_message
from app.models.models import TelegramUser, UserEngagementEvent, OutboundMessage
from app.enums.db_enums import DeliveryChannelEnum, EngagementStateEnum, EntityTypeEnum


async def send_telegram_and_log(
    db: Session,
    *,
    user_id,
    session_id,
    text: str,
    message_type: str,
    buttons=None,
    source: str = "system",
):
    tg = (
        db.query(TelegramUser)
        .filter_by(user_id=user_id, opt_in=True)
        .first()
    )
    if not tg:
        return None

    engagement = UserEngagementEvent(
        user_id=user_id,
        session_id=session_id,
        entity_type=EntityTypeEnum.user_session,
        entity_id=session_id,
        channel=DeliveryChannelEnum.telegram,
        state=EngagementStateEnum.unopened,
        event_metadata_data={
            "message_type": message_type,
            "source": source,
        },
    )
    db.add(engagement)
    db.flush()

    try:
        await send_telegram_message(
            chat_id=tg.chat_id,
            text=text,
            buttons=buttons,
        )
        engagement.state = EngagementStateEnum.sent
        status = "sent"
    except Exception:
        engagement.state = EngagementStateEnum.ignored
        status = "failed"

    outbound = OutboundMessage(
        user_id=user_id,
        session_id=session_id,
        channel=DeliveryChannelEnum.telegram,
        engagement_event_id=engagement.id,
        message_type=message_type,
        content=text[:1000],
        status=status,
    )
    db.add(outbound)
    db.commit()
    return outbound

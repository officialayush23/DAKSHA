# app/services/event_service.py
import uuid
from sqlalchemy.orm import Session
from app.models.models import Event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum

def emit_event(
    db: Session,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    channel: str,
    event_type: EventTypeEnum,
    entity_type: EntityTypeEnum,
    entity_id: uuid.UUID = None,
    quantity: int = None,
    price: float = None,
    reason: str = None,
    metadata: dict = None,
):
    event = Event(
        id=uuid.uuid4(),
        user_id=user_id,
        session_id=session_id,
        channel=channel,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        quantity=quantity,
        price=price,
        reason=reason,
        event_metadata=metadata
    )
    db.add(event)
    db.commit()
    return event
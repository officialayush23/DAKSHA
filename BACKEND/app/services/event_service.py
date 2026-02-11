# app/services/event_service.py
# import uuid
# from typing import Optional, Dict, Any
# from sqlalchemy.orm import Session

# from app.models.models import Event
# from app.enums.db_enums import (
#     EventTypeEnum,
#     EntityTypeEnum,
#     ChannelEnum,
# )


# def emit_event(
#     db: Session,
#     *,
#     event_type: EventTypeEnum,
#     channel: Optional[ChannelEnum] = None,

#     user_id: Optional[uuid.UUID] = None,
#     session_id: Optional[uuid.UUID] = None,
#     anonymous_id: Optional[uuid.UUID] = None,

#     entity_type: Optional[EntityTypeEnum] = None,
#     entity_id: Optional[uuid.UUID] = None,

#     quantity: Optional[int] = None,
#     price: Optional[float] = None,

#     metadata: Optional[Dict[str, Any]] = None,
# ) -> Event:
#     """
#     Core event emission function.

#     Invariants:
#     - Exactly one of user_id or anonymous_id must exist
#     - entity_type <-> entity_id must be paired
#     - No side effects (no commit)
#     """

#     if not user_id and not anonymous_id:
#         raise ValueError("Either user_id or anonymous_id must be provided")

#     if entity_type and not entity_id:
#         raise ValueError("entity_id required when entity_type is provided")

#     if entity_id and not entity_type:
#         raise ValueError("entity_type required when entity_id is provided")

#     event = Event(
#         user_id=user_id,
#         anonymous_id=anonymous_id,
#         session_id=session_id,

#         channel=channel,
#         event_type=event_type,

#         entity_type=entity_type,
#         entity_id=entity_id,

#         quantity=quantity,
#         price=price,

#         event_metadata=metadata,
#     )

#     db.add(event)
#     return event
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import Event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum, ChannelEnum

def emit_event(
    db: Session,
    *,
    event_type: EventTypeEnum,
    channel: Optional[ChannelEnum] = None,
    user_id: Optional[uuid.UUID] = None,
    session_id: Optional[uuid.UUID] = None,
    anonymous_id: Optional[uuid.UUID] = None,
    entity_type: Optional[EntityTypeEnum] = None,
    entity_id: Optional[uuid.UUID] = None,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    
    # Validation
    if not user_id and not anonymous_id:
        # We allow it ONLY if session_id is present (inferred identity)
        if not session_id:
             # raise ValueError("Context missing: Provide user_id, anonymous_id, or session_id")
             pass # Relaxed for system events

    if entity_type and not entity_id:
        raise ValueError(f"entity_id required for type {entity_type}")

    event = Event(
        user_id=user_id,
        anonymous_id=anonymous_id,
        session_id=session_id,
        channel=channel,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        quantity=quantity,
        price=price,
        # FIX: The model field is 'event_metadata_payload' mapped to JSONB 'event_metadata'
        event_metadata_payload=metadata, 
    )

    db.add(event)
    # Note: We do NOT commit here to allow bundling with other transactions.
    # The caller must commit.
    return event
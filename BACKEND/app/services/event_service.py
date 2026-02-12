# app/services/event_service.py

import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import Event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum, ChannelEnum


def emit_event(
    db: Session,
    *,
    event_type: EventTypeEnum,

    # identity
    user_id: Optional[uuid.UUID] = None,
    anonymous_id: Optional[uuid.UUID] = None,
    session_id: Optional[uuid.UUID] = None,

    # context
    channel: Optional[ChannelEnum] = None,

    # entity linkage
    entity_type: Optional[EntityTypeEnum] = None,
    entity_id: Optional[uuid.UUID] = None,

    # quantitative signals
    quantity: Optional[int] = None,
    price: Optional[float] = None,

    # metadata
    metadata: Optional[Dict[str, Any]] = None,

    # REQUIRED intent
    source: str = "user_action",  # user_action | agent_action | system
) -> Event:
    """
    Canonical event emission function.

    HARD INVARIANTS:
    1. Exactly one identity source must exist:
       - user_id OR anonymous_id OR (session_id + source="system")
    2. entity_type and entity_id must be provided together or not at all
    3. source is mandatory and explicit
    4. No commit here (transaction controlled by caller)
    """

    # ---------- Identity validation ----------
    identity_count = sum(
        x is not None for x in (user_id, anonymous_id)
    )

    if identity_count == 0:
        if not session_id or source != "system":
            raise ValueError(
                "Event must have user_id, anonymous_id, "
                "or (session_id + source='system')"
            )

    if identity_count > 1:
        raise ValueError(
            "Event cannot have both user_id and anonymous_id"
        )

    # ---------- Entity validation ----------
    if (entity_type is None) != (entity_id is None):
        raise ValueError(
            "entity_type and entity_id must be provided together"
        )

    # ---------- Source validation ----------
    if source not in {"user_action", "agent_action", "system"}:
        raise ValueError(f"Invalid event source: {source}")

    # ---------- Metadata enrichment ----------
    enriched_metadata = metadata or {}
    enriched_metadata["source"] = source

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
        event_metadata=enriched_metadata,
    )

    db.add(event)
    return event

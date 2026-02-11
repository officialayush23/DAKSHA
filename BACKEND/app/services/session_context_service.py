
# app/services/session_context_service.py
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from app.models.models import UserSession

ALLOWED_KEYS = {
    "current_intent",
    "funnel_stage",
    "detected_constraints",
    "last_product_viewed",
    "last_agent_action",
    "confidence",
}

def update_session_context(
    db: Session,
    session_id: UUID,
    updates: Dict[str, Any],
):
    session = db.get(UserSession, session_id)
    if not session:
        return None

    context = session.context or {}

    for k, v in updates.items():
        if k in ALLOWED_KEYS:
            context[k] = v

    session.context = context
    db.commit()
    return context

def get_session_context(
    db: Session,
    session_id: UUID,
) -> Dict[str, Any]:
    session = db.get(UserSession, session_id)
    if not session:
        return {}
    return session.context or {}

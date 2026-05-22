# app/services/chat_session_service.py
"""
Chat session management:
  - create / get / list sessions
  - append messages
  - rolling context (last 10 msgs + older summary)
  - AI-generated session name after first message
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.models import ChatSession, ChatMessage


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_session(db: Session, user_id: str, channel: str = "web") -> ChatSession:
    session = ChatSession(
        user_id=uuid.UUID(user_id),
        channel=channel,
        name=None,          # named by AI after first message
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str, user_id: str) -> Optional[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.id == uuid.UUID(session_id),
            ChatSession.user_id == uuid.UUID(user_id),
        )
        .first()
    )


def list_sessions(db: Session, user_id: str, limit: int = 50) -> List[ChatSession]:
    """Return sessions newest-first."""
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == uuid.UUID(user_id))
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )


def set_session_name(db: Session, session_id: str, name: str):
    db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).update(
        {"name": name, "updated_at": datetime.utcnow()}
    )
    db.commit()


# ── Messages ──────────────────────────────────────────────────────────────────

def append_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    tool_name: Optional[str] = None,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=uuid.UUID(session_id),
        role=role,
        content=content,
        tool_name=tool_name,
    )
    db.add(msg)
    db.commit()
    return msg


def get_messages(db: Session, session_id: str, limit: int = 200) -> List[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == uuid.UUID(session_id))
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


# ── Rolling context ───────────────────────────────────────────────────────────
RECENT_WINDOW = 10   # messages sent to LLM raw
SUMMARY_TRIGGER = 20 # summarise when total exceeds this


def get_context_for_llm(db: Session, session_id: str) -> dict:
    """
    Returns:
      {
        "summary": str | None,          # compressed history of older messages
        "recent_messages": [            # last RECENT_WINDOW messages
            {"role": "user"|"assistant", "content": str}, ...
        ]
      }
    Only the recent messages + summary are sent to the LLM each turn.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == uuid.UUID(session_id)
    ).first()
    if not session:
        return {"summary": None, "recent_messages": []}

    all_msgs = get_messages(db, session_id)

    if len(all_msgs) <= RECENT_WINDOW:
        return {
            "summary": session.summary,
            "recent_messages": [{"role": m.role, "content": m.content} for m in all_msgs],
        }

    recent    = all_msgs[-RECENT_WINDOW:]
    to_summarise = all_msgs[:-RECENT_WINDOW]

    return {
        "summary": session.summary,
        "recent_messages": [{"role": m.role, "content": m.content} for m in recent],
        "older_count": len(to_summarise),
    }


def update_rolling_summary(db: Session, session_id: str, new_summary: str):
    """Called after each turn to compress older messages into the session summary."""
    db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).update(
        {"summary": new_summary, "updated_at": datetime.utcnow()}
    )
    db.commit()


# ── AI naming ────────────────────────────────────────────────────────────────

def generate_session_name(first_user_message: str) -> str:
    """
    Generate a short session name from the first user message using Gemini.
    Falls back to a truncated version of the message if LLM fails.
    """
    try:
        from app.ai.llm import get_gemini
        llm = get_gemini(temperature=0.3)
        prompt = (
            f"Generate a very short name (3-5 words max) for a customer support chat "
            f"that starts with this message: '{first_user_message[:200]}'\n"
            f"Reply with only the name, no quotes, no explanation."
        )
        from langchain_core.messages import HumanMessage
        result = llm.invoke([HumanMessage(content=prompt)])
        name = result.content.strip().strip('"').strip("'")[:80]
        return name if name else _fallback_name(first_user_message)
    except Exception:
        return _fallback_name(first_user_message)


def _fallback_name(message: str) -> str:
    words = message.strip().split()
    return " ".join(words[:5]) + ("…" if len(words) > 5 else "")

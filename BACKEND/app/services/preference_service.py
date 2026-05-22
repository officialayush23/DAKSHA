# app/services/preference_service.py
"""
User Preference Summary Service
────────────────────────────────
After each chat turn, this background service:
  1. Pulls the last N messages for this user from the session
  2. Calls Gemini to distil a short taste-profile paragraph
  3. Embeds it with Nomic
  4. Upserts user_preference_summary  (one row per user, PK = user_id)

This vector powers:
  • personalised recall (ANN on user_preference_summary.embedding)
  • context injection into recommendation agent system prompt
"""
import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import SessionLocal
from app.models.models import UserPreferenceSummary, ChatSession, ChatMessage
from app.services.embedding_service import generate_text_embedding

logger = logging.getLogger(__name__)

# ── how many recent conversation summaries to look at
_LOOKBACK_SUMMARIES = 5

# ── Gemini distillation prompt
_DISTIL_PROMPT = """
You are a fashion taste-profile extractor for DAKSHA.
Below is a recent conversation between a user and the Daksha shopping concierge.
Distil it into ONE tight paragraph (≤80 words) capturing:
  - preferred styles, categories, colours, occasions
  - price sensitivity
  - brands they like or dislike
  - any size/fit notes

Output ONLY the paragraph — no headers, no bullet points.

Conversation:
{summaries}
""".strip()


async def refresh_user_preference_summary(
    user_id: str,
    session_id: Optional[str] = None,
) -> None:
    """
    Fire-and-forget background task called after each chat turn.
    Failures are silently logged — they must never break the chat response.
    """
    try:
        with SessionLocal() as db:
            await _do_refresh(db, user_id, session_id)
    except Exception as e:
        logger.warning(f"⚠️ preference_service: refresh failed for user {user_id}: {e}")


async def _do_refresh(db: Session, user_id: str, session_id: Optional[str]) -> None:
    # 1. Pull the last N user+assistant messages across all of this user's chat sessions
    rows = (
        db.query(ChatMessage.role, ChatMessage.content, ChatMessage.created_at)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .filter(
            ChatSession.user_id == uuid.UUID(user_id),
            ChatMessage.role.in_(["user", "assistant"]),
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(30)
        .all()
    )

    if not rows:
        return  # nothing to learn from yet

    # Format as a short conversation transcript (oldest first)
    lines = [
        f"{r.role.upper()}: {r.content[:300]}"
        for r in reversed(rows)
        if r.content
    ]
    summaries_text = "\n".join(lines)
    if not summaries_text.strip():
        return

    # 2. Call Gemini Flash to distil taste profile
    summary_paragraph = await _call_gemini_distil(summaries_text)
    if not summary_paragraph:
        return

    # 3. Embed the paragraph
    embedding = generate_text_embedding(summary_paragraph)

    # 4. Upsert (one row per user)
    stmt = pg_insert(UserPreferenceSummary).values(
        user_id=uuid.UUID(user_id),
        summary_text=summary_paragraph,
        embedding=embedding,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id"],
        set_={
            "summary_text": stmt.excluded.summary_text,
            "embedding":    stmt.excluded.embedding,
            "updated_at":   db.execute("SELECT now()").scalar() if False else None,
        },
    )
    # Simpler approach — just merge / update directly
    existing = db.get(UserPreferenceSummary, uuid.UUID(user_id))
    if existing:
        existing.summary_text = summary_paragraph
        existing.embedding    = embedding
    else:
        db.add(UserPreferenceSummary(
            user_id=uuid.UUID(user_id),
            summary_text=summary_paragraph,
            embedding=embedding,
        ))

    db.commit()
    logger.info(f"✅ preference_service: updated summary for user {user_id}")


async def _call_gemini_distil(summaries_text: str) -> Optional[str]:
    """Uses Gemini Flash (via Vertex AI) to produce a compact taste-profile paragraph."""
    try:
        from langchain_core.messages import HumanMessage
        from app.ai.llm import get_gemini

        llm = get_gemini(temperature=0.2)
        prompt = _DISTIL_PROMPT.format(summaries=summaries_text[:3000])
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip() or None
    except Exception as e:
        logger.warning(f"preference_service: Gemini distil failed: {e}")
        return None

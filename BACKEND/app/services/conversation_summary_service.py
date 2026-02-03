# app/services/conversation_summary_service.py
from sqlalchemy.orm import Session
from app.models.models import Conversation, ConversationSummary
from app.services.embedding_service import generate_embedding

MAX_MESSAGES = 30

def update_conversation_summary(db: Session, session_id):
    messages = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.desc())
        .limit(MAX_MESSAGES)
        .all()
    )

    if not messages:
        return

    text = " | ".join(
        f"{m.speaker}: {m.message}"
        for m in reversed(messages)
    )

    embedding = generate_embedding(text)

    summary = (
        db.query(ConversationSummary)
        .filter(ConversationSummary.session_id == session_id)
        .first()
    )

    if summary:
        summary.summary_text = text
        summary.embedding = embedding
    else:
        db.add(
            ConversationSummary(
                session_id=session_id,
                summary_text=text,
                embedding=embedding,
            )
        )

    db.commit()

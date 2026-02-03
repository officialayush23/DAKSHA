# app/services/embedding_service.py
from sqlalchemy.orm import Session
from app.models.models import UserPreferenceSummary, Event, Product, ProductVariant, ProductEmbedding
from app.core.config import settings
from google import genai
from google.genai import types
# app/services/embedding_service.py
import numpy as np

# Gemini client (official SDK)
client = genai.Client(api_key=settings.GEMINI_API_KEY)

EMBED_DIM = 768


def generate_embedding(text: str) -> list[float]:
    """
    Generate a normalized 768-dim embedding using Gemini.
    This is the ONLY low-level embedding function.
    """
    if not text or not text.strip():
        return [0.0] * EMBED_DIM

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBED_DIM
        ),
    )

    values = np.array(response.embeddings[0].values, dtype=float)
    norm = np.linalg.norm(values)

    if norm == 0:
        return values.tolist()

    return (values / norm).tolist()


def update_user_preference_summary(db: Session, user_id):
    """
    Builds a rolling semantic profile of the user.
    """

    events = (
        db.query(Event)
        .filter(Event.user_id == user_id)
        .order_by(Event.created_at.desc())
        .limit(50)
        .all()
    )

    if not events:
        return

    summary_text = " | ".join(
        f"{e.event_type} {e.entity_type} {e.reason or ''}"
        for e in events
    )

    embedding = generate_embedding(summary_text)

    pref = (
        db.query(UserPreferenceSummary)
        .filter(UserPreferenceSummary.user_id == user_id)
        .first()
    )

    if pref:
        pref.summary_text = summary_text
        pref.embedding = embedding
    else:
        db.add(
            UserPreferenceSummary(
                user_id=user_id,
                summary_text=summary_text,
                embedding=embedding,
            )
        )

    db.commit()


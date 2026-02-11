# app/services/embedding_service.py
import os
import nomic
from nomic import embed
from sqlalchemy.orm import Session
from app.models.models import UserPreferenceSummary, Event, ProductVariant, ProductEmbedding
from app.core.config import settings
# Init
nomic.login(settings.NOMIC_API_KEY)

TEXT_MODEL = "nomic-embed-text-v1.5"
VISION_MODEL = "nomic-embed-vision-v1.5"
TASK_TYPE = "search_document"
DIM = 768


def generate_text_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        return [0.0] * DIM

    try:
        res = embed.text(
            texts=[text],
            model=TEXT_MODEL,
            task_type=TASK_TYPE,
            dimensionality=DIM,
        )
        return res["embeddings"][0]
    except Exception as e:
        print(f"[TEXT EMBEDDING ERROR] {e}")
        return [0.0] * DIM


def generate_image_embedding(image_url_or_path: str) -> list[float]:
    try:
        res = embed.image(
            images=[image_url_or_path],
            model=VISION_MODEL,
        )
        return res["embeddings"][0]
    except Exception as e:
        print(f"[IMAGE EMBEDDING ERROR] {e}")
        return [0.0] * DIM

def update_user_preference_summary(db: Session, user_id):
    """
    Builds a rolling semantic profile of the user based on recent events.
    """
    # 1. Fetch last 50 significant events
    events = (
        db.query(Event)
        .filter(Event.user_id == user_id)
        .order_by(Event.created_at.desc())
        .limit(50)
        .all()
    )

    if not events:
        return

    # 2. Construct a narrative text for the user's intent
    # e.g., "viewed Red Shirt | searched for 'Summer Wear' | added Blue Jeans to cart"
    summary_parts = []
    for e in events:
        action = e.event_type.replace("_", " ")
        entity = e.event_metadata_payload.get('product_name', 'item') if e.event_metadata_payload else 'item'
        summary_parts.append(f"{action} {entity}")
    
    summary_text = " | ".join(summary_parts)

    # 3. Embed this narrative
    embedding = generate_text_embedding(summary_text)

    # 4. Upsert into DB
    pref = db.query(UserPreferenceSummary).filter(UserPreferenceSummary.user_id == user_id).first()
    
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
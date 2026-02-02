# app/services/embedding_service.py
from sqlalchemy.orm import Session
from app.models.models import UserPreferenceSummary, Event, Product, ProductVariant, ProductEmbedding
from app.core.config import settings
from google import genai
from google.genai import types

# Create Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_embedding(text: str) -> list[float]:
    """
    Generate a 768-dim embedding using Gemini (official SDK).
    Renamed from 'embed_text' to match your consumers.
    """
    if not text or not text.strip():
        return [0.0] * 768

    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=768
            ),
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Gemini Embedding Error: {e}")
        return [0.0] * 768

def update_user_preference_summary(db: Session, user_id):
    """
    Builds a semantic profile of the user based on recent events.
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

    # Create a narrative for the LLM/Embedding model
    summary_text = "User recent history: " + " | ".join(
        f"{e.event_type} {e.entity_type} ({e.reason or ''})"
        for e in events
    )

    embedding = generate_embedding(summary_text)

    pref = db.query(UserPreferenceSummary).filter(UserPreferenceSummary.user_id == user_id).first()
    
    if pref:
        pref.summary_text = summary_text
        pref.embedding = embedding
    else:
        pref = UserPreferenceSummary(
            user_id=user_id,
            summary_text=summary_text,
            embedding=embedding,
        )
        db.add(pref)

    db.commit()

def upsert_product_variant_embedding(db: Session, variant_id):
    """
    Generates embedding for a product variant based on its attributes.
    """
    variant = db.query(ProductVariant).join(Product).filter(ProductVariant.id == variant_id).first()
    if not variant: return

    product = variant.product
    
    # Deterministic semantic text
    text = f"{product.brand} {product.category} {product.gender} {product.description} Color: {variant.color} Size: {variant.size}"
    
    embedding = generate_embedding(text)

    existing = db.query(ProductEmbedding).filter(ProductEmbedding.product_variant_id == variant.id).first()
    if existing:
        existing.embedding = embedding
    else:
        db.add(ProductEmbedding(product_variant_id=variant.id, embedding=embedding))
    
    db.commit()
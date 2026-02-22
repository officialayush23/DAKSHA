# app/services/user_preference_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from google import genai
from google.genai import types


from app.core.config import settings
from app.services.embedding_service import generate_text_embedding

genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL = "gemini-2.5-flash"
def build_user_preference_summary(db: Session, user_id: str):
    rows = db.execute(text("""
        SELECT event_type, event_metadata
        FROM events
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT 150
    """), {"uid": user_id}).fetchall()

    if not rows:
        return

    lines = []
    for r in rows:
        meta = r.event_metadata or {}
        name = meta.get("product_name") or meta.get("category") or "item"
        lines.append(f"{r.event_type} → {name}")

    history = "\n".join(lines)

    prompt = f"""
Analyze this shopper behavior and return JSON:

{{
  "preferred_categories": [],
  "preferred_colors": [],
  "preferred_sizes": [],
  "price_min": number | null,
  "price_max": number | null,
  "style_summary": "short description"
}}

DATA:
{history}
"""

    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2
        )
    )

    text_out = resp.text

    import json
    data = json.loads(text_out)

    summary = data.get("style_summary", "")

    embedding = generate_text_embedding(summary)

    # upsert semantic profile
    db.execute(text("""
        INSERT INTO user_preference_summary
        (user_id, summary_text, embedding, updated_at)
        VALUES (:uid, :summary, :emb, NOW())
        ON CONFLICT (user_id)
        DO UPDATE SET
            summary_text = EXCLUDED.summary_text,
            embedding = EXCLUDED.embedding,
            updated_at = NOW()
    """), {
        "uid": user_id,
        "summary": summary,
        "emb": str(embedding),
    })

    # upsert structured preferences
    db.execute(text("""
        INSERT INTO user_preferences (
            user_id,
            preferred_categories,
            preferred_colors,
            preferred_sizes,
            preferred_price_min,
            preferred_price_max,
            updated_by
        )
        VALUES (
            :uid,
            :cats,
            :colors,
            :sizes,
            :pmin,
            :pmax,
            'ai'
        )
        ON CONFLICT (user_id)
        DO UPDATE SET
            preferred_categories = EXCLUDED.preferred_categories,
            preferred_colors = EXCLUDED.preferred_colors,
            preferred_sizes = EXCLUDED.preferred_sizes,
            preferred_price_min = EXCLUDED.preferred_price_min,
            preferred_price_max = EXCLUDED.preferred_price_max,
            updated_at = NOW()
    """), {
        "uid": user_id,
        "cats": data.get("preferred_categories"),
        "colors": data.get("preferred_colors"),
        "sizes": data.get("preferred_sizes"),
        "pmin": data.get("price_min"),
        "pmax": data.get("price_max"),
    })

    db.commit()
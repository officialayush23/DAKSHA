# app/services/user_preference_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from google import genai
from google.genai import types
import json
import re

from app.core.config import settings
from app.services.embedding_service import generate_text_embedding

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL = "gemini-2.5-flash"
def build_user_preference_summary(db: Session, user_id: str):
    try:
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

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2)
        )

        import json, re

        raw = resp.text.strip()
        match = re.search(r'\{.*\}', raw, re.S)
        if not match:
            raise ValueError("Model did not return JSON")

        data = json.loads(match.group())

        def ensure_list(v):
            if v is None:
                return None
            if isinstance(v, list):
                return v
            return [v]

        def to_num(v):
            try:
                return float(v) if v is not None else None
            except:
                return None

        summary = data.get("style_summary", "")

        embedding = generate_text_embedding(summary)
        
        # upsert semantic summary + embedding
        db.execute(text("""
        INSERT INTO user_preference_summary (
            user_id,
            summary_text,
            embedding,
            updated_at
        )
        VALUES (
            :uid,
            :summary,
            :embedding,
            NOW()
        )
        ON CONFLICT (user_id)
        DO UPDATE SET
            summary_text = EXCLUDED.summary_text,
            embedding = EXCLUDED.embedding,
            updated_at = NOW()
        """), {
            "uid": user_id,
            "summary": summary,
            "embedding": embedding,   # IMPORTANT: pass list, NOT string
        })

        db.execute(text("""
INSERT INTO user_preferences (
    user_id,
    preferred_categories,
    preferred_colors,
    preferred_sizes,
    preferred_price_min,
    preferred_price_max,
    updated_by,
    last_preference_refresh
)
VALUES (
    :uid,
    :cats,
    :colors,
    :sizes,
    :pmin,
    :pmax,
    'ai',
    NOW()
)
ON CONFLICT (user_id)
DO UPDATE SET
    preferred_categories = EXCLUDED.preferred_categories,
    preferred_colors = EXCLUDED.preferred_colors,
    preferred_sizes = EXCLUDED.preferred_sizes,
    preferred_price_min = EXCLUDED.preferred_price_min,
    preferred_price_max = EXCLUDED.preferred_price_max,
    last_preference_refresh = NOW(),
    updated_at = NOW()
"""), {
            "uid": user_id,
            "cats": ensure_list(data.get("preferred_categories")),
            "colors": ensure_list(data.get("preferred_colors")),
            "sizes": ensure_list(data.get("preferred_sizes")),
            "pmin": to_num(data.get("price_min")),
            "pmax": to_num(data.get("price_max")),
        })

        db.commit()

    except Exception as e:
        db.rollback()
        print("Preference build failed:", e)
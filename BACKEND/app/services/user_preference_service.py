# app/services/user_preference_service.py
# app/services/user_preference_service.py
import json
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.embedding_service import generate_text_embedding
from app.models.models import UserPreferences 

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"

def build_user_preference_summary(db: Session, user_id: str):
    print(f"\n{'='*50}\n🚀 [AI PREF] STARTING FOR USER {user_id}\n{'='*50}")
    
    try:
        # 👇 FIXED: JOIN events with products to get actual names, colors, and categories!
        rows = db.execute(text("""
            SELECT 
                e.event_type, 
                e.event_metadata,
                COALESCE(p.name, p_meta.name) as product_name,
                COALESCE(p.category, p_meta.category) as category,
                COALESCE(p.brand, p_meta.brand) as brand,
                COALESCE(pv.color, pv_meta.color) as color,
                COALESCE(pv.size, pv_meta.size) as size,
                COALESCE(pv.base_price, pv_meta.base_price) as price
            FROM events e
            
            -- Join for events where entity_id IS the variant_id (e.g. wishlist)
            LEFT JOIN product_variants pv ON e.entity_type = 'product_variant' AND e.entity_id = pv.id
            LEFT JOIN products p ON pv.product_id = p.id
            
            -- Join for events where variant_id is hidden inside event_metadata JSON (e.g. cart)
            LEFT JOIN product_variants pv_meta ON e.event_metadata->>'variant_id' IS NOT NULL 
                AND length(e.event_metadata->>'variant_id') = 36
                AND (e.event_metadata->>'variant_id')::uuid = pv_meta.id
            LEFT JOIN products p_meta ON pv_meta.product_id = p_meta.id
            
            WHERE e.user_id = :uid
            ORDER BY e.created_at DESC
            LIMIT 150
        """), {"uid": user_id}).fetchall()

        if not rows:
            print(f"⚠️ [AI PREF] No events found. Exiting.")
            return

        # Translate database rows into human-readable English for Gemini
        lines = []
        for r in rows:
            meta = r.event_metadata or {}
            
            # Handle standard text searches
            if r.event_type == 'search' and 'query' in meta:
                lines.append(f"Searched for: '{meta['query']}'")
                continue
                
            # Handle Product interactions
            details = []
            if r.product_name: details.append(r.product_name)
            if r.category: details.append(f"Category: {r.category}")
            if r.brand: details.append(f"Brand: {r.brand}")
            if r.color: details.append(f"Color: {r.color}")
            if r.size: details.append(f"Size: {r.size}")
            if r.price: details.append(f"Price: ₹{r.price}")
            
            if details:
                item_desc = " | ".join(details)
                lines.append(f"{r.event_type} -> {item_desc}")

        history = "\n".join(lines)
        print(f"📖 [AI PREF] HISTORY SENT TO AI:\n{history}\n")

        if not lines:
            print("⚠️ [AI PREF] No actionable product interactions found. Exiting.")
            return

        prompt = f"""
        Analyze this shopper behavior and return a strict JSON object.
        
        Format:
        {{
          "preferred_categories": ["string"],
          "preferred_colors": ["string"],
          "preferred_sizes": ["string"],
          "price_min": 100,
          "price_max": 5000,
          "style_summary": "string"
        }}

        Extract all unique categories, colors, and sizes the user interacted with.
        Calculate the approximate min and max price they look at.
        Do not include markdown in the response.
        
        DATA:
        {history}
        """

        # Ask Gemini to analyze the history
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json", 
            )
        )

        raw = resp.text.strip()
        print(f"🤖 [AI PREF] GEMINI JSON RESPONSE:\n{raw}\n")

        # Fallback regex in case Gemini wraps the JSON in markdown
        match = re.search(r'\{.*\}', raw, re.S)
        if not match:
            raise ValueError("Model did not return valid JSON")
        
        data = json.loads(match.group())

        # Safely extract lists and numbers
        def ensure_list(v):
            if not v: return []
            if isinstance(v, list): return [str(i) for i in v if i]
            return [str(v)]

        def to_num(v):
            try: 
                val = float(v)
                return val if val > 0 else None
            except: 
                return None

        summary = data.get("style_summary") or "General shopper"
        embedding = generate_text_embedding(summary)
        
        print("💾 [AI PREF] Upserting semantic summary...")
        db.execute(text("""
        INSERT INTO user_preference_summary (
            user_id, summary_text, embedding, updated_at
        ) VALUES (:uid, :summary, :embedding, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            summary_text = EXCLUDED.summary_text,
            embedding = EXCLUDED.embedding,
            updated_at = NOW()
        """), {
            "uid": user_id,
            "summary": summary,
            "embedding": embedding,
        })

        print("💾 [AI PREF] Upserting explicit preferences to ORM...")
        pref = db.query(UserPreferences).filter_by(user_id=user_id).first()
        if not pref:
            pref = UserPreferences(user_id=user_id)
            db.add(pref)

        pref.preferred_categories = ensure_list(data.get("preferred_categories"))
        pref.preferred_colors = ensure_list(data.get("preferred_colors"))
        pref.preferred_sizes = ensure_list(data.get("preferred_sizes"))
        pref.preferred_price_min = to_num(data.get("price_min"))
        pref.preferred_price_max = to_num(data.get("price_max"))
        pref.updated_by = 'ai'
        
        # 👇 Ensure timezone aware so it doesn't default to NULL
        pref.last_preference_refresh = datetime.now(timezone.utc)

        db.commit()
        print(f"✅ [AI PREF] SUCCESS! Preferences updated for {user_id}\n{'='*50}")

    except Exception as e:
        db.rollback()
        print(f"❌ [AI PREF] ERROR for user {user_id}: {e}\n{'='*50}")
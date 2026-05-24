# app/services/embedding_service.py
import os
import nomic
from nomic import embed
from sqlalchemy.orm import Session
from app.models.models import UserPreferenceSummary, Event, ProductVariant, ProductMultimodalEmbedding
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
    """
    Generate a vision embedding for an image.

    Accepts a local file path OR a Supabase storage URL.
    For Supabase URLs the file is downloaded via the service-role SDK client
    (bypasses RLS, works for private buckets) and written to a temp file so
    Nomic embed.image() can read it from disk.
    """
    import os, tempfile, mimetypes

    _STORAGE_MARKER = "/storage/v1/object/public/"

    tmp_path = None
    try:
        if image_url_or_path.startswith("http") and _STORAGE_MARKER in image_url_or_path:
            # ── Supabase storage URL: use SDK to download (works for private buckets) ──
            from app.services.storage_service import supabase as _sb_admin

            tail = image_url_or_path.split(_STORAGE_MARKER, 1)[1]   # "bucket/filename.ext"
            bucket, _, file_path = tail.partition("/")
            file_path = file_path.split("?")[0]                       # strip query params

            file_bytes = _sb_admin.storage.from_(bucket).download(file_path)

            # Determine extension from file path
            ext = os.path.splitext(file_path)[1] or ".jpg"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            target = tmp_path

        elif image_url_or_path.startswith("http"):
            # ── Generic public URL: plain httpx fetch ──
            import httpx
            resp = httpx.get(image_url_or_path, timeout=20, follow_redirects=True)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "image/jpeg")
            if "json" in ct or "html" in ct:
                raise ValueError(f"Expected image bytes, got content-type: {ct}")
            ext = ".png" if "png" in ct else ".webp" if "webp" in ct else ".gif" if "gif" in ct else ".jpg"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
            target = tmp_path

        else:
            # ── Local file path ──
            target = image_url_or_path

        res = embed.image(images=[target], model=VISION_MODEL)
        return res["embeddings"][0]

    except Exception as e:
        print(f"[IMAGE EMBEDDING ERROR] {e}")
        return [0.0] * DIM
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

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
        entity = (e.event_metadata or {}).get("product_name", "item")
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
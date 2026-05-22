# app/services/candidate_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List

from app.services.embedding_service import generate_text_embedding


def generate_candidates(
    db: Session,
    user_id: str,
    intent_text: Optional[str] = None,
    limit: int = 300,
    seed_variant_id: Optional[str] = None,
) -> List[str]:
    """
    Phase 1: HYBRID RECALL

    Sources (intent-based search uses STRICT semantic only):
    • semantic similarity (intent or preference)
    • collaborative ML signals  — skipped when intent_text is set
    • PDP seed similarity       — for product detail page "similar items"
    • trending fallback         — skipped when intent_text is set
    """

    candidates = set()
    has_intent = bool(intent_text and intent_text.strip())

    # --------------------------------------------------
    # 1️⃣ SEMANTIC RECALL (intent OR taste profile)
    # --------------------------------------------------
    vec = generate_text_embedding(intent_text) if has_intent else None

    if not vec and user_id:
        pref = db.execute(
            text("""
                SELECT embedding
                FROM user_preference_summary
                WHERE user_id = :uid
            """),
            {"uid": user_id},
        ).first()
        vec = pref[0] if pref else None

    if vec:
        if has_intent:
            # Strict mode: apply cosine distance threshold (< 0.55 ≈ similarity > 0.45)
            # This filters out semantically unrelated products from intent-based search
            rows = db.execute(text("""
                SELECT product_variant_id
                FROM product_multimodal_embeddings
                WHERE modality = 'text'
                  AND embedding <=> CAST(:vec AS vector) < 0.55
                ORDER BY embedding <=> CAST(:vec AS vector)
                LIMIT 200
            """), {"vec": vec}).fetchall()
        else:
            # Home feed: top-N without threshold (broader discovery)
            rows = db.execute(text("""
                SELECT product_variant_id
                FROM product_multimodal_embeddings
                WHERE modality = 'text'
                ORDER BY embedding <=> CAST(:vec AS vector)
                LIMIT 150
            """), {"vec": vec}).fetchall()

        candidates.update(str(r[0]) for r in rows)

    # --------------------------------------------------
    # 2️⃣ COLLABORATIVE FILTERING (taste neighbors)
    # Skip for intent search — collab dilutes precision
    # --------------------------------------------------
    if user_id and not has_intent:
        try:
            from app.services.ml_service import get_collaborative_candidates  # lazy — torch optional
            collab_ids = get_collaborative_candidates(user_id, k=100)
            candidates.update(str(vid) for vid in collab_ids)
        except Exception:
            pass

    # --------------------------------------------------
    # 3️⃣ PDP SEED SIMILARITY
    # enables: similar items on product page
    # --------------------------------------------------
    if seed_variant_id:
        rows = db.execute(text("""
            SELECT product_variant_id_b
            FROM product_affinities
            WHERE product_variant_id_a = :vid
            ORDER BY score DESC
            LIMIT 120
        """), {"vid": seed_variant_id}).fetchall()

        candidates.update(str(r[0]) for r in rows)

    # --------------------------------------------------
    # 4️⃣ TRENDING SAFETY NET
    # Ensures home feed is never empty.
    # Skip for intent search — trending dilutes precision.
    # --------------------------------------------------
    if not has_intent and len(candidates) < 60:
        rows = db.execute(text("""
            SELECT product_variant_id
            FROM trending_products
            WHERE scope = 'all'
            ORDER BY rank_position ASC
            LIMIT 100
        """)).fetchall()

        candidates.update(str(r[0]) for r in rows)

    return list(candidates)[:limit]
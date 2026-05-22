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

    Sources:
    • semantic similarity (intent or preference)
    • collaborative ML signals
    • PDP seed similarity (NEW)
    • trending fallback
    """

    candidates = set()

    # --------------------------------------------------
    # 1️⃣ SEMANTIC RECALL (intent OR taste profile)
    # --------------------------------------------------
    vec = generate_text_embedding(intent_text) if intent_text else None

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
    # --------------------------------------------------
    if user_id:
        try:
            from app.services.ml_service import get_collaborative_candidates  # lazy — torch optional
            collab_ids = get_collaborative_candidates(user_id, k=100)
            candidates.update(str(vid) for vid in collab_ids)
        except Exception:
            pass

    # --------------------------------------------------
    # 3️⃣ PDP SEED SIMILARITY (NEW)
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
    # ensures feed never empty
    # --------------------------------------------------
    if len(candidates) < 60:
        rows = db.execute(text("""
            SELECT product_variant_id
            FROM trending_products
            WHERE scope = 'all'
            ORDER BY rank_position ASC
            LIMIT 100
        """)).fetchall()

        candidates.update(str(r[0]) for r in rows)

    return list(candidates)[:limit]
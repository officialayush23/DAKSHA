# app/services/candidate_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import generate_text_embedding
from app.services.ml_service import get_collaborative_candidates

def generate_candidates(db: Session, user_id: str, intent_text: str = None, limit: int = 300):
    """
    Phase 1: RECALL. Fetches a wide net of variants from Semantic, ML, and Trending sources.
    """
    candidates = set()

    # --- 1. SEMANTIC RECALL ---
    vec = generate_text_embedding(intent_text) if intent_text else None
    if not vec and user_id:
        pref = db.execute(
            text("SELECT embedding FROM user_preference_summary WHERE user_id = :uid"), 
            {"uid": user_id}
        ).first()
        vec = pref[0] if pref else None
    
    if vec:
        rows = db.execute(text("""
            SELECT product_variant_id 
            FROM product_multimodal_embeddings
            WHERE modality = 'text' 
            ORDER BY embedding <=> :vec
            LIMIT 150
        """), {"vec": str(vec)}).fetchall()
        candidates.update([str(r[0]) for r in rows])

    # --- 2. ML COLLABORATIVE RECALL ---
    if user_id:
        try:
            collab_ids = get_collaborative_candidates(user_id, k=100)
            candidates.update([str(vid) for vid in collab_ids])
        except Exception:
            pass

    # --- 3. TRENDING FALLBACK ---
    rows = db.execute(text("""
        SELECT product_variant_id 
        FROM trending_products
        WHERE scope = 'global' 
        ORDER BY rank_position ASC 
        LIMIT 100
    """)).fetchall()
    candidates.update([str(r[0]) for r in rows])

    return list(candidates)[:limit]
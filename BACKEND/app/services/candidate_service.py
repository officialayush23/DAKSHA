# app/services/candidate_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.ml_service import get_collaborative_candidates

def generate_candidates(db: Session, user_id: str, intent_text: str = None, limit: int = 200):
    candidates = set()

    # 1. Collaborative Filtering (PyTorch Model) - Behavior
    # "People who bought what you bought also bought X"
    collab_ids = get_collaborative_candidates(user_id, k=limit)
    candidates.update(collab_ids)

    # 2. Content-Based (Vector Search) - Semantic Preference
    # "Items matching your long-term style"
    # Note: We only select IDs here, no complex joining
    query_content = text("""
        SELECT product_variant_id 
        FROM user_preference_summary ups
        JOIN product_embeddings pe ON 1=1
        WHERE ups.user_id = :uid
        ORDER BY pe.embedding <=> ups.embedding
        LIMIT :lim
    """)
    rows = db.execute(query_content, {"uid": user_id, "lim": limit}).fetchall()
    candidates.update([str(r[0]) for r in rows])

    # 3. Trending (Cold Start Fallback)
    # "What is popular right now"
    query_trend = text("SELECT product_variant_id FROM category_trending ORDER BY rank_position LIMIT 50")
    rows = db.execute(query_trend).fetchall()
    candidates.update([str(r[0]) for r in rows])

    # 4. Explicit Intent (If user is searching/chatting)
    if intent_text:
        # Vector search on the intent text
        # (Assuming you have a function to get embedding, or use pgvector query directly if intent_vec passed)
        pass 

    return list(candidates)
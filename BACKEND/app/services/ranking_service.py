# app/services/ranking_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import generate_embedding

def rank_candidates(db: Session, user_id: str, candidate_ids: list[str], intent_text: str = None, limit: int = 20):
    if not candidate_ids:
        return []

    # Generate Intent Vector (if applicable)
    intent_vector = generate_embedding(intent_text) if intent_text else [0.0]*768

    # Dynamic Weights (Context-Aware)
    if intent_text:
        W = {"content": 0.1, "collab": 0.1, "intent": 0.7, "trend": 0.1}
    else:
        W = {"content": 0.4, "collab": 0.4, "intent": 0.0, "trend": 0.2}

    # Format list for SQL
    candidate_list_str = "{" + ",".join(candidate_ids) + "}"

    query = text(f"""
        WITH 
        UserPref AS (
            SELECT COALESCE(embedding, array_fill(0, ARRAY[768])::vector) as vec 
            FROM user_preference_summary WHERE user_id = :uid
        ),
        IntentVec AS (SELECT :intent_vec::vector AS vec)

        SELECT 
            p.id, p.brand, p.description, p.category,
            pv.id as variant_id, pv.base_price,
            pi.image_url,
            
            -- SCORING
            (1 - (pe.embedding <=> (SELECT vec FROM UserPref))) AS content_score,
            (1 - (pe.embedding <=> (SELECT vec FROM IntentVec))) AS intent_score,
            
            -- Trend (Inverse Rank)
            COALESCE((SELECT (1.0 / rank_position) FROM category_trending WHERE product_variant_id = pv.id), 0) AS trend_score

        FROM product_variants pv
        JOIN products p ON pv.product_id = p.id
        JOIN product_embeddings pe ON pv.id = pe.product_variant_id
        LEFT JOIN product_images pi ON pi.product_variant_id = pv.id AND pi.position = 1
        
        -- CRITICAL: Only score the candidates!
        WHERE pv.id::text = ANY(:candidates) AND p.active = true
        
        ORDER BY (
            (:wc * (1 - (pe.embedding <=> (SELECT vec FROM UserPref)))) + 
            (:wi * (1 - (pe.embedding <=> (SELECT vec FROM IntentVec)))) +
            (:wcol * 0.5) + -- (Simplified collab score, assuming existence in set = relevant)
            (:wt * COALESCE((SELECT (1.0 / rank_position) FROM category_trending WHERE product_variant_id = pv.id), 0))
        ) DESC
        LIMIT :limit
    """)

    results = db.execute(query, {
        "uid": user_id,
        "intent_vec": str(intent_vector),
        "candidates": list(candidate_ids), # SQLAlchemy handles Array conversion
        "wc": W['content'],
        "wi": W['intent'],
        "wcol": W['collab'],
        "wt": W['trend'],
        "limit": limit
    }).fetchall()

    return results
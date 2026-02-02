# app/services/recommendation_service.py
# from sqlalchemy.orm import Session
# from sqlalchemy import text
# from app.services.embedding_service import generate_embedding
# from app.services.ml_service import get_collaborative_candidates

# def get_hybrid_recommendations(db: Session, user_id: str, intent_text: str = None, limit: int = 20):
#     # 1. Get Collaborative Candidates (TensorFlow)
#     # These are products similar users liked.
#     tf_candidates = get_collaborative_candidates(user_id, k=50)
    
#     # 2. Get Vectors (Content-Based)
#     intent_vector = generate_embedding(intent_text) if intent_text else [0.0]*768
    
#     # 3. Hybrid Query
#     # We use the TF candidates to filter the search space (Candidate Generation),
#     # then use Vector similarity + Logic to Re-rank them.
    
#     # If TF model is cold (empty), we fallback to pure Content/Trending.
#     if not tf_candidates:
#         tf_filter_clause = "1=1" # No filter
#     else:
#         # We explicitly boost these items in the sort order
#         formatted_ids = "', '".join(tf_candidates)
#         tf_filter_clause = f"pv.id IN ('{formatted_ids}')"

#     # Weights
#     ALPHA_CONTENT = 0.4
#     BETA_COLLAB = 0.3 # Boost for items found by TF
#     GAMMA_TREND = 0.1
#     ZETA_INTENT = 0.2 if intent_text else 0.0

#     query = text(f"""
#         WITH 
#         UserPref AS (SELECT embedding::vector AS vec FROM user_preference_summary WHERE user_id = :uid),
#         IntentVec AS (SELECT :intent_vec::vector AS vec)

#         SELECT 
#             p.id, 
#             p.brand, 
#             p.description,
#             pv.id as variant_id,
#             pv.base_price,
#             pi.image_url,
            
#             -- SCORING
#             (1 - (pe.embedding <=> (SELECT vec FROM UserPref))) AS content_score,
            
#             -- Collab Score: 1.0 if recommended by TF model, else 0.0
#             CASE WHEN pv.id::text = ANY(:tf_candidates) THEN 1.0 ELSE 0.0 END AS collab_score,

#             -- Trend Score
#             COALESCE((SELECT (1.0 / rank_position) FROM category_trending WHERE product_variant_id = pv.id), 0) AS trend_score,

#             -- Intent Score
#             (1 - (pe.embedding <=> (SELECT vec FROM IntentVec))) AS intent_score

#         FROM product_variants pv
#         JOIN products p ON pv.product_id = p.id
#         JOIN product_embeddings pe ON pv.id = pe.product_variant_id
#         LEFT JOIN product_images pi ON pi.product_variant_id = pv.id AND pi.position = 1
#         WHERE p.active = true
        
#         -- Hybrid Sort Equation
#         ORDER BY (
#             (:alpha * (1 - (pe.embedding <=> COALESCE((SELECT vec FROM UserPref), array_fill(0, ARRAY[768])::vector)))) + 
#             (:beta  * CASE WHEN pv.id::text = ANY(:tf_candidates) THEN 1.0 ELSE 0.0 END) + 
#             (:gamma * COALESCE((SELECT (1.0 / rank_position) FROM category_trending WHERE product_variant_id = pv.id), 0)) +
#             (:zeta  * (1 - (pe.embedding <=> (SELECT vec FROM IntentVec))))
#         ) DESC
#         LIMIT :limit
#     """)

#     results = db.execute(query, {
#         "uid": str(user_id),
#         "intent_vec": str(intent_vector),
#         "tf_candidates": tf_candidates,
#         "alpha": ALPHA_CONTENT,
#         "beta": BETA_COLLAB,
#         "gamma": GAMMA_TREND,
#         "zeta": ZETA_INTENT,
#         "limit": limit
#     }).fetchall()

#     return [
#         {
#             "product_id": row.id,
#             "brand": row.brand,
#             "variant_id": row.variant_id,
#             "price": row.base_price,
#             "image": row.image_url,
#             "scores": {
#                 "content": row.content_score,
#                 "collab": row.collab_score,
#                 "intent": row.intent_score
#             }
#         } 
#         for row in results
#     ]

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import generate_embedding
from app.services.ml_service import get_collaborative_candidates

def get_hybrid_recommendations(db: Session, user_id: str, intent_text: str = None, limit: int = 20):
    
    # 1. Get Behavioral Candidates (from PyTorch)
    # Returns a list of ['uuid-1', 'uuid-2']
    collab_candidates = get_collaborative_candidates(user_id, k=50)
    
    # 2. Get Semantic Vector (from Gemini)
    intent_vector = generate_embedding(intent_text) if intent_text else [0.0]*768

    # 3. Dynamic Weights (Heuristics)
    # If explicit intent exists, boost it massiveley. 
    # If no intent, rely on history (Content + Collab).
    if intent_text:
        W_CONTENT = 0.2
        W_COLLAB = 0.1
        W_INTENT = 0.6  # User just asked for something specific
        W_TREND = 0.1
    else:
        W_CONTENT = 0.4
        W_COLLAB = 0.4  # Rely on behavior
        W_INTENT = 0.0
        W_TREND = 0.2

    # 4. The Ensemble Query
    # We construct a Postgres array from the collab candidates to check membership efficienty
    collab_array_literal = "{" + ",".join(collab_candidates) + "}" if collab_candidates else "{}"

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
            
            -- SCORING COMPONENTS
            (1 - (pe.embedding <=> (SELECT vec FROM UserPref))) AS content_score,
            (1 - (pe.embedding <=> (SELECT vec FROM IntentVec))) AS intent_score,
            
            -- Collab Score (1.0 if in top-50 candidates, else 0)
            CASE WHEN pv.id::text = ANY(:collab_list) THEN 1.0 ELSE 0.0 END AS collab_score,

            -- Trend Score (Inverse Rank)
            COALESCE((SELECT (1.0 / rank_position) FROM category_trending WHERE product_variant_id = pv.id), 0) AS trend_score

        FROM product_variants pv
        JOIN products p ON pv.product_id = p.id
        JOIN product_embeddings pe ON pv.id = pe.product_variant_id
        LEFT JOIN product_images pi ON pi.product_variant_id = pv.id AND pi.position = 1
        WHERE p.active = true
        
        ORDER BY (
            (:w_content * (1 - (pe.embedding <=> (SELECT vec FROM UserPref)))) + 
            (:w_collab  * CASE WHEN pv.id::text = ANY(:collab_list) THEN 1.0 ELSE 0.0 END) + 
            (:w_trend   * COALESCE((SELECT (1.0 / rank_position) FROM category_trending WHERE product_variant_id = pv.id), 0)) +
            (:w_intent  * (1 - (pe.embedding <=> (SELECT vec FROM IntentVec))))
        ) DESC
        LIMIT :limit
    """)

    results = db.execute(query, {
        "uid": str(user_id),
        "intent_vec": str(intent_vector),
        "collab_list": list(collab_candidates), # SQL Alchemy handles list -> Array conversion usually, or use literal above
        "w_content": W_CONTENT,
        "w_collab": W_COLLAB,
        "w_trend": W_TREND,
        "w_intent": W_INTENT,
        "limit": limit
    }).fetchall()

    return [
        {
            "product_id": row.id,
            "brand": row.brand,
            "category": row.category,
            "variant_id": row.variant_id,
            "price": row.base_price,
            "image": row.image_url,
            "debug_scores": {
                "content": row.content_score,
                "collab": row.collab_score,
                "intent": row.intent_score,
                "trend": row.trend_score
            }
        } 
        for row in results
    ]
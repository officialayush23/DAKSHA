# app/services/recommendation_service.py
# from sqlalchemy.orm import Session
# from sqlalchemy import text, func, desc
# from app.services.embedding_service import generate_text_embedding
# from app.services.impression_service import log_impressions
# from app.models.models import ProductVariant, Product, UserPreferenceSummary
# from app.services.pricing_service import resolve_variant_price

# def get_hybrid_recommendations(
#     db: Session, 
#     user_id: str, 
#     intent_text: str = None, 
#     session_id: str = None,
#     limit: int = 20
# ):
#     candidates = []
    
#     # 1. Vector Search
#     query_vec = None
#     if intent_text:
#         query_vec = generate_text_embedding(intent_text)
#     else:
#         # Use User History from the table we just added to models.py
#         user_pref = db.query(UserPreferenceSummary).filter_by(user_id=user_id).first()
#         if user_pref and user_pref.embedding:
#             query_vec = user_pref.embedding

#     if query_vec:
#         vector_str = str(query_vec)
#         semantic_query = text(f"""
#             SELECT pv.id, 1 - (pe.embedding <=> '{vector_str}') as score, 'semantic' as reason
#             FROM product_variants pv
#             JOIN product_multimodal_embeddings pe ON pv.id = pe.product_variant_id
#             WHERE pe.modality = 'text'
#             ORDER BY pe.embedding <=> '{vector_str}'
#             LIMIT :limit
#         """)
#         rows = db.execute(semantic_query, {"limit": limit}).fetchall()
#         candidates.extend([dict(row._mapping) for row in rows])

#     # 2. Trending Fallback
#     if len(candidates) < limit:
#         # Corrected Table Name: trending_products
#         trending_query = text("""
#             SELECT product_variant_id as id, trending_score as score, 'trending' as reason
#             FROM trending_products
#             WHERE scope = 'global'
#             ORDER BY rank_position ASC
#             LIMIT :limit
#         """)
#         rows = db.execute(trending_query, {"limit": limit - len(candidates)}).fetchall()
#         candidates.extend([dict(row._mapping) for row in rows])

#     # 3. Hydrate
#     final_results = []
#     seen = set()
#     for c in candidates:
#         if c['id'] in seen: continue
#         seen.add(c['id'])
        
#         variant = db.query(ProductVariant).get(c['id'])
#         if not variant: continue
        
#         price = resolve_variant_price(db, variant)

#         final_results.append({
#             "variant_id": variant.id,
#             "product_id": variant.product_id,
#             "name": variant.product.name,
#             "brand": variant.product.brand,
#             "category": variant.product.category,
#             "base_price": price["base_price"],
#             "final_price": price["final_price"],
#             "offer_name": price["offer_name"],
#             "score": float(c.get("score", 0.0)),
#             "reason": c["reason"],
#         })

    
#     return final_results[:limit]
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import generate_text_embedding
from app.services.impression_service import log_impressions
from app.models.models import ProductVariant, UserPreferenceSummary
from app.services.pricing_service import resolve_variant_price
from app.services.postrank_service import apply_business_rules

# --- EXACT WEIGHT CONFIGURATION ---
WEIGHT_SEMANTIC = 0.5      
WEIGHT_COLLABORATIVE = 0.3 
WEIGHT_TRENDING = 0.2      

def get_hybrid_recommendations(
    db: Session, 
    user_id: str, 
    intent_text: str = None, 
    session_id: str = None,
    limit: int = 20
):
    master_scores = {} 

    # 1. SEMANTIC / INTENT RECALL (Weight: 0.5)
    query_vec = None
    if intent_text:
        query_vec = generate_text_embedding(intent_text)
    else:
        user_pref = db.query(UserPreferenceSummary).filter_by(user_id=user_id).first()
        if user_pref and user_pref.embedding:
            query_vec = user_pref.embedding

    if query_vec:
        vector_str = str(query_vec)
        semantic_query = text(f"""
            SELECT pv.id, 1 - (pe.embedding <=> '{vector_str}') as semantic_score
            FROM product_variants pv
            JOIN product_multimodal_embeddings pe ON pv.id = pe.product_variant_id
            WHERE pe.modality = 'text' AND pv.active = true
            ORDER BY pe.embedding <=> '{vector_str}'
            LIMIT 100
        """)
        rows = db.execute(semantic_query).fetchall()
        for row in rows:
            vid = str(row.id)
            master_scores[vid] = master_scores.get(vid, 0.0) + (float(row.semantic_score) * WEIGHT_SEMANTIC)

    # 2. COLLABORATIVE RECALL (Weight: 0.3)
    # Hooks into your PyTorch TwoTowerModel. For safe fallback if model isn't trained yet, we mock an empty dict.
    from app.services.ml_service import get_collaborative_candidates
    try:
        collab_ids = get_collaborative_candidates(user_id, k=50)
        for i, vid in enumerate(collab_ids):
            score = 1.0 - (i / len(collab_ids)) # Rough normalization
            master_scores[vid] = master_scores.get(vid, 0.0) + (score * WEIGHT_COLLABORATIVE)
    except Exception:
        pass

    # 3. TRENDING RECALL (Weight: 0.2)
    trending_query = text("""
        SELECT product_variant_id, trending_score
        FROM trending_products
        WHERE scope = 'global'
        ORDER BY rank_position ASC
        LIMIT 50
    """)
    t_rows = db.execute(trending_query).fetchall()
    for row in t_rows:
        vid = str(row.product_variant_id)
        master_scores[vid] = master_scores.get(vid, 0.0) + (float(row.trending_score) * WEIGHT_TRENDING)

    # 4. RANK & HYDRATE
    ranked_variant_ids = sorted(master_scores.keys(), key=lambda v: master_scores[v], reverse=True)
    
    raw_results = []
    for vid in ranked_variant_ids:
        variant = db.query(ProductVariant).get(vid)
        if not variant: continue
        raw_results.append(variant)

    # 5. POST-RANK (Business Rules & Diversity)
    diversified = apply_business_rules(raw_results)[:limit]

    # 6. FORMAT & PRICING
    final_feed = []
    for variant in diversified:
        price = resolve_variant_price(db, variant)
        final_feed.append({
            "variant_id": variant.id,
            "product_id": variant.product_id,
            "name": variant.product.name,
            "brand": variant.product.brand,
            "category": variant.product.category,
            "image": variant.images[0].image_url if variant.images else None,
            "base_price": price["base_price"],
            "final_price": price["final_price"],
            "offer_name": price["offer_name"],
            "score": master_scores[str(variant.id)],
            "reason": "hybrid_weighted",
        })

    # 7. LOG IMPRESSIONS
    log_impressions(db, user_id, final_feed, feed_type="search" if intent_text else "home", session_id=session_id)

    return final_feed


def get_similar_variants(db: Session, variant_id: str, user_id: str = None, limit: int = 10):
    target_vec_sql = text("SELECT embedding FROM product_multimodal_embeddings WHERE product_variant_id = :vid AND modality = 'text' LIMIT 1")
    target_row = db.execute(target_vec_sql, {"vid": variant_id}).first()
    
    if not target_row or not target_row.embedding:
        return []
        
    vector_str = str(target_row.embedding)
    semantic_query = text(f"""
        SELECT pv.id, 1 - (pe.embedding <=> '{vector_str}') as score, 'similar' as reason
        FROM product_variants pv
        JOIN product_multimodal_embeddings pe ON pv.id = pe.product_variant_id
        WHERE pe.modality = 'text' AND pv.active = true AND pv.id != :vid
        ORDER BY pe.embedding <=> '{vector_str}'
        LIMIT :limit
    """)
    
    rows = db.execute(semantic_query, {"vid": variant_id, "limit": limit}).fetchall()
    
    results = []
    for r in rows:
        variant = db.query(ProductVariant).get(r.id)
        if not variant: continue
        price = resolve_variant_price(db, variant)
        results.append({
            "variant_id": variant.id,
            "product_id": variant.product_id,
            "name": variant.product.name,
            "image": variant.images[0].image_url if variant.images else None,
            "base_price": price["base_price"],
            "final_price": price["final_price"],
            "score": float(r.score),
            "reason": r.reason
        })
    return results
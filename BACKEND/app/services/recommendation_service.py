# app/services/recommendation_service.py
# from sqlalchemy.orm import Session
# from sqlalchemy import text, func, desc
# from app.services.embedding_service import generate_text_embedding
# from app.services.impression_service import log_impressions
# from app.services.offer_service import attach_offers_to_products
# from app.models.models import ProductVariant, Product, ProductEmbedding, ProductAffinity, UserPreferenceSummary

# def get_hybrid_recommendations(
#     db: Session, 
#     user_id: str, 
#     intent_text: str = None, 
#     session_id: str = None,
#     limit: int = 20
# ):
#     """
#     The Core Engine. Combines Vector Search (Semantics) + Graph (Affinities) + Trending.
#     """
    
#     # --- 1. Generate Query Vector ---
#     # If user has specific intent ("Red shoes"), use that.
#     # Otherwise, use their long-term preference profile.
#     if intent_text:
#         query_vec = generate_text_embedding(intent_text)
#         vector_source = "intent_text"
#     else:
#         user_pref = db.query(UserPreferenceSummary).filter_by(user_id=user_id).first()
#         if user_pref and user_pref.embedding:
#             query_vec = user_pref.embedding
#             vector_source = "user_history"
#         else:
#             query_vec = None
#             vector_source = "trending_fallback"

#     candidates = []

#     # --- 2. Vector Search (Semantic Recall) ---
#     # Finds items visually/textually similar to the query
#     if query_vec:
#         # Postgres pgvector cosine distance (<=>)
#         # Note: We cast the python list to a vector string for SQL
#         vector_str = str(query_vec)
        
#         semantic_query = text(f"""
#             SELECT 
#                 pv.id, 
#                 1 - (pe.embedding <=> '{vector_str}') as score,
#                 'semantic' as reason
#             FROM product_variants pv
#             JOIN product_embeddings pe ON pv.id = pe.product_variant_id
#             JOIN products p ON pv.product_id = p.id
#             WHERE p.active = true AND pv.active = true
#             ORDER BY pe.embedding <=> '{vector_str}'
#             LIMIT :limit
#         """)
        
#         rows = db.execute(semantic_query, {"limit": limit}).fetchall()
#         candidates.extend([dict(row._mapping) for row in rows])

#     # --- 3. Graph Search (Bought Together) ---
#     # If we found semantic candidates, let's boost items often bought with them
#     if candidates:
#         top_variant_ids = [str(c['id']) for c in candidates[:5]]
        
#         if top_variant_ids:
#             affinity_query = text(f"""
#                 SELECT 
#                     product_variant_id_b as id,
#                     score,
#                     'bought_together' as reason
#                 FROM product_affinities
#                 WHERE product_variant_id_a = ANY(:ids)
#                 ORDER BY score DESC
#                 LIMIT 10
#             """)
            
#             rows = db.execute(affinity_query, {"ids": top_variant_ids}).fetchall()
#             candidates.extend([dict(row._mapping) for row in rows])

#     # --- 4. Fallback: Trending ---
#     if len(candidates) < limit:
#         trending_query = text("""
#             SELECT 
#                 product_variant_id as id, 
#                 trending_score as score,
#                 'trending' as reason
#             FROM trending_products 
#             WHERE scope = 'global'
#             ORDER BY rank_position ASC
#             LIMIT :limit
#         """)
#         rows = db.execute(trending_query, {"limit": limit - len(candidates)}).fetchall()
#         candidates.extend([dict(row._mapping) for row in rows])

#     # --- 5. Hydrate & Format ---
#     # We now have IDs. Let's fetch full details + Offers.
#     final_results = []
#     seen_ids = set()

#     for cand in candidates:
#         vid = cand['id']
#         if vid in seen_ids: continue
#         seen_ids.add(vid)

#         variant = db.query(ProductVariant).get(vid)
#         if not variant: continue

#         # Format for Frontend/Agent
#         item = {
#             "product_id": variant.product_id,
#             "variant_id": variant.id,
#             "name": variant.product.name,
#             "brand": variant.product.brand,
#             "category": variant.product.category,
#             "price": float(variant.base_price),
#             "image": variant.images[0].image_url if variant.images else None,
#             "reason": cand['reason'], # Important for Agent Explanation
#             "score": float(cand['score']) if cand['score'] else 0.0
#         }
#         final_results.append(item)

#     # Attach Discounts (Loyalty/Offers)
#     final_results = attach_offers_to_products(db, final_results)

#     # --- 6. Log Impressions (The Data Flywheel) ---
#     log_impressions(
#         db, 
#         user_id, 
#         final_results, 
#         feed_type="search" if intent_text else "home", 
#         session_id=session_id
#     )

#     return final_results[:limit]


from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID

from app.services.embedding_service import generate_text_embedding
from app.services.impression_service import log_impressions
from app.services.offer_service import attach_offers_to_products
from app.services.ml_service import get_collaborative_candidates
from app.models.models import (
    ProductVariant, Product, ProductReviewStat, 
    UserBehaviorAggregate, UserPreferences, UserPreferenceSummary
)

# Configuration
PRICE_TOLERANCE = 0.4  # +/- 40% of average spend
MIN_RATING_THRESHOLD = 3.5

def get_hybrid_recommendations(
    db: Session, 
    user_id: str, 
    intent_text: str = None, 
    session_id: str = None, 
    limit: int = 20
):
    """
    Full Pipeline: Recall -> Filter (Price/Review) -> Rank -> Hydrate -> Log
    """
    
    # --- 1. PREPARE CONSTRAINTS (Price Band & Reviews) ---
    behavior = db.query(UserBehaviorAggregate).get(user_id)
    # Default price range (wide open if no history)
    min_price, max_price = 0, 1000000
    if behavior and behavior.avg_viewed_price and not intent_text:
        # If user has history and NOT specifically searching, enforce budget
        avg_price = float(behavior.avg_viewed_price)
        min_price = avg_price * (1 - PRICE_TOLERANCE)
        max_price = avg_price * (1 + PRICE_TOLERANCE)

    # --- 2. RECALL (Candidate Generation) ---
    candidates = {} # {variant_id: score}

    # A. Semantic Recall (Vector)
    query_vec = None
    if intent_text:
        query_vec = generate_text_embedding(intent_text)
    else:
        # Use rolling profile
        pref = db.query(UserPreferenceSummary).get(user_id)
        if pref and pref.embedding:
            query_vec = pref.embedding

    if query_vec:
        vec_str = str(query_vec)
        # HNSW Semantic Search
        sem_sql = text(f"""
            SELECT product_variant_id, (1 - (embedding <=> '{vec_str}')) as score 
            FROM product_multimodal_embeddings 
            WHERE modality = 'text' 
            ORDER BY embedding <=> '{vec_str}' LIMIT 50
        """)
        for row in db.execute(sem_sql):
            candidates[str(row.product_variant_id)] = float(row.score)

    # B. Collaborative Recall (PyTorch Model)
    # Fills the "You might also like" based on user patterns
    if not intent_text:
        ml_ids = get_collaborative_candidates(user_id, k=50)
        for vid in ml_ids:
            # Add or boost existing score
            candidates[str(vid)] = candidates.get(str(vid), 0.0) + 0.2

    # C. Trending Fallback (Cold Start)
    if len(candidates) < 10:
        trend_sql = text("SELECT product_variant_id FROM trending_products WHERE scope='global' ORDER BY rank_position LIMIT 20")
        for row in db.execute(trend_sql):
            vid = str(row.product_variant_id)
            candidates[vid] = candidates.get(vid, 0.0) + 0.1

    # --- 3. FILTER & RANK (In-Database) ---
    candidate_ids = list(candidates.keys())
    if not candidate_ids:
        return []

    # Join with Review Stats and Variants to filter
    rank_query = text("""
        SELECT 
            pv.id as variant_id, pv.base_price as price,
            p.id as product_id, p.name, p.brand, p.category,
            pi.image_url,
            COALESCE(rs.avg_rating, 0) as rating,
            COALESCE(rs.review_count, 0) as reviews
        FROM product_variants pv
        JOIN products p ON pv.product_id = p.id
        LEFT JOIN product_review_stats rs ON p.id = rs.product_id
        LEFT JOIN product_images pi ON pi.product_variant_id = pv.id AND pi.position = 1
        WHERE pv.id = ANY(:ids)
          AND pv.active = true
          -- FILTER 1: Review Quality (Skip bad products)
          AND (COALESCE(rs.avg_rating, 5) >= :min_rating)
          -- FILTER 2: Price Band (Skip items way out of budget)
          AND (pv.base_price BETWEEN :min_price AND :max_price)
    """)

    rows = db.execute(rank_query, {
        "ids": candidate_ids,
        "min_rating": MIN_RATING_THRESHOLD,
        "min_price": min_price,
        "max_price": max_price
    }).fetchall()

    # --- 4. SCORING ---
    final_items = []
    for row in rows:
        vid = str(row.variant_id)
        base_score = candidates.get(vid, 0)
        
        # Boost highly rated items with many reviews
        rating_boost = 1.0 + (0.1 if row.rating > 4.5 and row.reviews > 10 else 0)
        
        final_items.append({
            "variant_id": row.variant_id,
            "product_id": row.product_id,
            "name": row.name,
            "brand": row.brand,
            "category": row.category,
            "price": float(row.price),
            "image": row.image_url,
            "rating": float(row.rating),
            "match_score": base_score * rating_boost,
            "reason": "semantic" if intent_text else "recommended"
        })

    # Sort by Final Score
    final_items.sort(key=lambda x: x["match_score"], reverse=True)
    
    # --- 5. PRICING & LOGGING ---
    # Apply Catalog Discounts & Personalized Offers logic
    final_items = attach_offers_to_products(db, final_items[:limit])

    log_impressions(db, user_id, final_items, feed_type="hybrid", session_id=session_id)

    return final_items
# app/services/ranking_service.py
# app/services/ranking_service.py

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import generate_embedding

# NOTE:
# Collaborative filtering is used at recall-time (candidate generation).
# Ranking focuses on semantic + intent + trend for stability.

def rank_candidates(
    db: Session,
    user_id: str,
    candidate_ids: list[str],
    intent_text: str | None = None,
    limit: int = 20,
):
    if not candidate_ids:
        return []

    # --------------------------------------------------
    # 1. Intent Vector (Python-side, NOT SQL-side)
    # --------------------------------------------------
    intent_vector = (
        generate_embedding(intent_text)
        if intent_text
        else [0.0] * 768
    )

    # --------------------------------------------------
    # 2. Dynamic Weights
    # --------------------------------------------------
    if intent_text:
        W = {
            "content": 0.1,
            "collab": 0.1,   # future-proofed
            "intent": 0.6,
            "trend": 0.2,
        }
    else:
        W = {
            "content": 0.4,
            "collab": 0.3,
            "intent": 0.0,
            "trend": 0.3,
        }

    # --------------------------------------------------
    # 3. SAFE SQL (NO :param::vector anywhere)
    # --------------------------------------------------
    query = text("""
        WITH
        UserPref AS (
            SELECT COALESCE(
                embedding,
                array_fill(0, ARRAY[768])::vector
            ) AS vec
            FROM user_preference_summary
            WHERE user_id = :uid
        ),

        IntentVec AS (
            SELECT vec
            FROM (SELECT :intent_vec AS vec) t
        ),

        RecentIntentBoost AS (
            SELECT entity_id, COUNT(*) AS interaction_count
            FROM user_intents
            WHERE user_id = :uid
              AND created_at > NOW() - INTERVAL '2 days'
            GROUP BY entity_id
        )

        SELECT
            p.id,
            p.brand,
            p.category,
            pv.id AS variant_id,
            pv.base_price,
            pi.image_url,

            (1 - (pe.embedding <=> (SELECT vec FROM UserPref)))  AS content_score,
            (1 - (pe.embedding <=> (SELECT vec FROM IntentVec))) AS intent_score,

            COALESCE(
                (SELECT (1.0 / rank_position)
                 FROM category_trending
                 WHERE product_variant_id = pv.id),
                0
            ) AS trend_score,

            COALESCE(rib.interaction_count, 0) AS intent_boost

        FROM product_variants pv
        JOIN products p ON pv.product_id = p.id
        JOIN product_embeddings pe ON pv.id = pe.product_variant_id
        LEFT JOIN product_images pi
            ON pi.product_variant_id = pv.id AND pi.position = 1
        LEFT JOIN RecentIntentBoost rib
            ON pv.id = rib.entity_id

        WHERE pv.id::text = ANY(:candidates)
          AND p.active = true

        ORDER BY (
            (:wc * (1 - (pe.embedding <=> (SELECT vec FROM UserPref)))) +
            (:wi * (1 - (pe.embedding <=> (SELECT vec FROM IntentVec)))) +
            (:wt * COALESCE(
                (SELECT (1.0 / rank_position)
                 FROM category_trending
                 WHERE product_variant_id = pv.id),
                0
            )) +
            (0.2 * COALESCE(rib.interaction_count, 0))
        ) DESC

        LIMIT :limit
    """)

    # --------------------------------------------------
    # 4. Execute (VECTOR PASSED AS VALUE, NOT CAST)
    # --------------------------------------------------
    results = db.execute(
        query,
        {
            "uid": user_id,
            "intent_vec": intent_vector,   # <-- IMPORTANT
            "candidates": list(candidate_ids),
            "wc": W["content"],
            "wi": W["intent"],
            "wt": W["trend"],
            "limit": limit,
        },
    ).fetchall()

    return results

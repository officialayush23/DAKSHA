# app/services/recommendation_service.py

import logging
from typing import Optional, List, Dict, Any

from app.core.database import supabase_admin
from app.services.ai_service import AIService
from app.services.promotion_service import PromotionService

logger = logging.getLogger("daksha.recommendation")


class RecommendationService:
    """
    Recommendation strategy (strict order):
    HOME (UX-facing, deterministic):
      - Inventory-backed trending (SAFE)
    ML (model-facing):
      - Precomputed embeddings
      - Live embeddings
      - Inventory + promotion aware ranking
    """

    # =========================================================
    # HOME — SAFE & DETERMINISTIC
    # =========================================================

    @staticmethod
    def for_home(user_context: dict, limit: int = 8) -> List[Dict]:
        """
        HARD GUARANTEE:
        - Never throws
        - Returns trending inventory if anything fails
        """
        try:
            return RecommendationService._trending_inventory(limit)
        except Exception:
            logger.exception("Home recommendation failed, returning empty list")
            return []

    @staticmethod
    def _trending_inventory(limit: int) -> List[Dict]:
        """
        Inventory-backed trending.
        Schema-safe. Never throws.
        """
        try:
            res = supabase_admin.rpc(
                "get_trending_products",
                {"p_limit": limit},
            ).execute()
            
            # ✅ FIX: Handle None response
            if not res or not res.data:
                return []

            rows = res.data

            return [
                {
                    "id": r["product_id"],
                    "name": r["name"],
                    "gender": r.get("gender"),
                    "image_url": r.get("image_url"),
                    "price": r.get("price_override") or r.get("base_price"),
                    "rating": r.get("avg_rating"),
                    "review_count": r.get("review_count"),
                    "badge": None,
                    "agent_reason": "Popular with customers",
                    "inventory": {
                        "available": (r.get("available_qty") or 0) > 0,
                        "quantity": r.get("available_qty", 0),
                    },
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Trending Inventory Error: {e}")
            return []

    # =========================================================
    # ML — PERSONALIZED PIPELINE
    # =========================================================

    @staticmethod
    def get_personalized_recommendations(
        user_id: Optional[str],
        limit: int = 8,
    ) -> List[Dict[str, Any]]:

        try:
            candidates: List[Dict[str, Any]] = []

            # ---------- 1. PRECOMPUTED EMBEDDING ----------
            if user_id:
                embedding = RecommendationService._get_precomputed_embedding(user_id)
                if embedding:
                    candidates = RecommendationService._rpc_recommend_by_vector(
                        embedding, limit * 2
                    )

            # ---------- 2. LIVE EMBEDDING (Fallback) ----------
            if not candidates and user_id:
                live_embedding = RecommendationService._compute_live_vector(user_id)
                if live_embedding:
                    candidates = RecommendationService._rpc_recommend_by_vector(
                        live_embedding, limit * 2
                    )

            # ---------- 3. INVENTORY FALLBACK ----------
            if not candidates:
                return RecommendationService._trending_inventory(limit)

            # ---------- INVENTORY FILTER ----------
            available = RecommendationService._filter_available_products(candidates)
            if not available:
                return RecommendationService._trending_inventory(limit)

            # ---------- PROMOTION AWARE RANKING ----------
            promotions = PromotionService.get_active_promotions()
            ranked = RecommendationService._rank_with_promotions(
                available, promotions
            )

            return ranked[:limit]

        except Exception:
            logger.exception("Personalized pipeline failed")
            # Fail-safe: return generic trending
            return RecommendationService._trending_inventory(limit)

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _get_precomputed_embedding(user_id: str) -> Optional[List[float]]:
        try:
            row = (
                supabase_admin.table("user_embeddings")
                .select("embedding")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            # ✅ FIX: Explicit None check
            if not row or not row.data:
                return None
            return row.data.get("embedding")
        except Exception as e:
            logger.warning(f"Failed to fetch embedding: {e}")
            return None

    @staticmethod
    def _rank_with_promotions(
        products: List[Dict[str, Any]],
        promotions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        ranked = []
        for p in products:
            promos = PromotionService.applicable_promotions_for_product(
                p, promotions
            )
            boost = 0.15 if promos else 0.0
            base_score = p.get("score", 1.0)

            ranked.append(
                {
                    **p,
                    "final_score": base_score + boost,
                    "applicable_promotions": promos,
                    "agent_reason": (
                        "Recommended based on your activity"
                        if promos
                        else "Matched to your interests"
                    ),
                }
            )

        ranked.sort(key=lambda x: x["final_score"], reverse=True)
        return ranked

    @staticmethod
    def _filter_available_products(
        recs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        product_ids = [r["product_id"] for r in recs if r.get("product_id")]
        if not product_ids:
            return []

        try:
            variants = (
                supabase_admin.table("product_variants")
                .select("id, product_id")
                .in_("product_id", product_ids)
                .execute()
            )
            
            if not variants or not variants.data:
                return []

            variant_ids = [v["id"] for v in variants.data]

            inventory = (
                supabase_admin.table("inventory")
                .select("product_variant_id")
                .in_("product_variant_id", variant_ids)
                .gt("quantity_on_hand", 0)
                .execute()
            )
            
            if not inventory or not inventory.data:
                return []

            available_variants = {i["product_variant_id"] for i in inventory.data}
            available_products = {
                v["product_id"]
                for v in variants.data
                if v["id"] in available_variants
            }

            return [r for r in recs if r.get("product_id") in available_products]
        
        except Exception as e:
            logger.error(f"Inventory filter error: {e}")
            return []

    # =========================================================
    # VECTOR OPS
    # =========================================================

    @staticmethod
    def _rpc_recommend_by_vector(vec: List[float], limit: int):
        try:
            res = supabase_admin.rpc(
                "recommend_products_by_vector",
                {
                    "query_embedding": vec,
                    "match_threshold": 0.55,
                    "match_count": limit,
                },
            ).execute()
            
            # ✅ FIX: None check
            if not res:
                return []
            return res.data or []
        except Exception:
            logger.exception("Vector RPC failed")
            return []

    @staticmethod
    def _compute_live_vector(user_id: str) -> Optional[List[float]]:
        try:
            footprints = (
                supabase_admin.table("user_facts")
                .select("value")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(12)
                .execute()
            )

            # ✅ FIX: None check
            if not footprints or not footprints.data:
                return None

            tokens = []
            for row in footprints.data:
                tokens.extend(
                    str(v)
                    for v in (row.get("event_data") or {}).values()
                    if isinstance(v, (str, int))
                )

            if not tokens:
                return None

            return AIService.generate_embedding(" ".join(tokens)[:1800])
        except Exception as e:
            logger.error(f"Live vector compute failed: {e}")
            return None
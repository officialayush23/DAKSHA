import logging
from typing import Optional, List, Dict, Any

from app.database import supabase
from app.services.ai_service import AIService
from app.services.promotion_service import PromotionService

logger = logging.getLogger("daksha.recommendation")


class RecommendationService:
    """
    Recommendation strategy (ordered):
    1) Precomputed user embedding
    2) Live embedding
    3) Trending fallback
    Promotion-aware, inventory-safe.
    """

    # =========================================================
    # PUBLIC API
    # =========================================================

    @staticmethod
    def get_personalized_recommendations(
        user_id: Optional[str], limit: int = 8
    ) -> List[Dict[str, Any]]:

        try:
            candidates: List[Dict[str, Any]] = []

            # ---------- 1) PRECOMPUTED EMBEDDING ----------
            if user_id:
                emb_row = (
                    supabase.table("user_embeddings")
                    .select("embedding")
                    .eq("user_id", user_id)
                    .maybe_single()
                    .execute()
                )

                embedding = emb_row.data.get("embedding") if emb_row.data else None

                if embedding:
                    recs = RecommendationService._rpc_recommend_by_vector(
                        embedding, limit * 2
                    )
                    candidates = recs or []

            # ---------- 2) LIVE EMBEDDING ----------
            if not candidates and user_id:
                live_embedding = RecommendationService._compute_live_vector(user_id)
                if live_embedding:
                    candidates = RecommendationService._rpc_recommend_by_vector(
                        live_embedding, limit * 2
                    ) or []

            # ---------- 3) TRENDING ----------
            if not candidates:
                candidates = RecommendationService.get_trending_products(limit * 2)

            if not candidates:
                return []

            # ---------- INVENTORY FILTER ----------
            filtered = RecommendationService._filter_available_products(candidates)
            if not filtered:
                return []

            # ---------- PROMOTION AWARE RANKING ----------
            promotions = PromotionService.get_active_promotions()
            enriched: List[Dict[str, Any]] = []

            for r in filtered:
                promos = PromotionService.applicable_promotions_for_product(
                    r, promotions
                )

                promo_boost = 0.15 if promos else 0.0
                base_score = r.get("score", 1.0)

                enriched.append(
                    {
                        **r,
                        "promo_score": promo_boost,
                        "final_score": base_score + promo_boost,
                        "applicable_promotions": [
                            {
                                "code": p["code"],
                                "discount_type": p["discount_type"],
                                "discount_value": p["discount_value"],
                                "summary": p["name"],
                            }
                            for p in promos
                        ],
                    }
                )

            enriched.sort(key=lambda x: x["final_score"], reverse=True)
            enriched = enriched[:limit]

            # ---------- AGENT EXPLANATIONS ----------
            context = (
                RecommendationService._get_user_context_text(user_id)
                if user_id
                else ""
            )

            final: List[Dict[str, Any]] = []
            for r in enriched:
                reason = RecommendationService._generate_agent_reason(r, context)
                final.append({**r, "agent_reason": reason})

            return final

        except Exception:
            logger.exception("Personalized recommendation pipeline failed")
            return RecommendationService.get_trending_products(limit)

    # =========================================================
    # PROMO + AGENT REASONING
    # =========================================================

    @staticmethod
    def _generate_agent_reason(rec: dict, user_context: str) -> str:
        reasons: List[str] = []

        if user_context:
            reasons.append(f"Based on recent interest: {user_context}")

        if rec.get("applicable_promotions"):
            p = rec["applicable_promotions"][0]
            reasons.append(
                f"Eligible for {p['code']} ({p['discount_value']} off)"
            )

        return " | ".join(reasons)

    # =========================================================
    # AVAILABILITY FILTERING
    # =========================================================

    @staticmethod
    def _filter_available_products(
        recs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        if not recs:
            return []

        product_ids = [r["id"] for r in recs if r.get("id")]
        if not product_ids:
            return []

        variants = (
            supabase.table("product_variants")
            .select("id, product_id")
            .in_("product_id", product_ids)
            .execute()
        ).data or []

        if not variants:
            return []

        variant_ids = [v["id"] for v in variants]

        inventory = (
            supabase.table("inventory")
            .select("product_variant_id")
            .in_("product_variant_id", variant_ids)
            .gt("quantity_on_hand", 0)
            .execute()
        ).data or []

        available_variants = {
            row["product_variant_id"] for row in inventory
        }

        available_products = {
            v["product_id"]
            for v in variants
            if v["id"] in available_variants
        }

        return [r for r in recs if r.get("id") in available_products]

    # =========================================================
    # VECTOR SEARCH
    # =========================================================

    @staticmethod
    def _rpc_recommend_by_vector(vec: List[float], limit: int):
        try:
            res = supabase.rpc(
                "recommend_products_by_vector",
                {
                    "query_embedding": vec,
                    "match_threshold": 0.55,
                    "match_count": limit,
                },
            ).execute()
            return res.data or []
        except Exception:
            logger.exception("Vector RPC failed")
            return []

    # =========================================================
    # LIVE USER CONTEXT
    # =========================================================

    @staticmethod
    def _compute_live_vector(user_id: str) -> Optional[List[float]]:
        footprints = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .order("captured_at", desc=True)
            .limit(12)
            .execute()
        )

        tokens: List[str] = []
        for row in footprints.data or []:
            ed = row.get("event_data") or {}
            tokens.extend(
                str(v) for v in ed.values() if isinstance(v, (str, int))
            )

        if not tokens:
            return None

        return AIService.generate_embedding(" ".join(tokens)[:1800])

    @staticmethod
    def _get_user_context_text(user_id: str) -> str:
        footprints = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .order("captured_at", desc=True)
            .limit(5)
            .execute()
        )

        parts = []
        for row in footprints.data or []:
            ed = row.get("event_data") or {}
            if ed.get("name"):
                parts.append(ed["name"])
            elif ed.get("query"):
                parts.append(ed["query"])

        return "; ".join(parts)

    # =========================================================
    # TRENDING
    # =========================================================

    @staticmethod
    def get_trending_products(limit: int = 8):
        try:
            res = (
                supabase.table("trending_products_weekly_cards")
                .select("*")
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception:
            logger.exception("Trending fallback failed")
            return []

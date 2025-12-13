# app/services/recommendation_service.py

import logging
from typing import Optional, List, Dict, Any

from app.database import supabase
from app.services.ai_service import AIService

logger = logging.getLogger("daksha.recommendation")


class RecommendationService:
    """
    Recommendation strategy (ordered):
    1) Precomputed user embedding (fast + stable)
    2) Live embedding from recent behavior
    3) Trending fallback
    All results are filtered by real inventory availability.
    """

    # =========================================================
    # PUBLIC API
    # =========================================================

    @staticmethod
    def get_personalized_recommendations(
        user_id: Optional[str], limit: int = 8
    ) -> List[Dict[str, Any]]:

        try:
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
                    if recs:
                        filtered = RecommendationService._filter_available_products(recs)
                        if filtered:
                            context = RecommendationService._get_user_context_text(
                                user_id
                            )
                            return RecommendationService._attach_explanations(
                                filtered[:limit], context
                            )

            # ---------- 2) LIVE EMBEDDING ----------
            if user_id:
                live_embedding = RecommendationService._compute_live_vector(user_id)
                if live_embedding:
                    recs = RecommendationService._rpc_recommend_by_vector(
                        live_embedding, limit * 2
                    )
                    if recs:
                        filtered = RecommendationService._filter_available_products(recs)
                        if filtered:
                            context = RecommendationService._get_user_context_text(
                                user_id
                            )
                            return RecommendationService._attach_explanations(
                                filtered[:limit], context
                            )

            # ---------- 3) TRENDING FALLBACK ----------
            trending = RecommendationService.get_trending_products(limit * 2)
            return RecommendationService._filter_available_products(trending)[:limit]

        except Exception:
            logger.exception("Personalized recommendation pipeline failed")
            return RecommendationService.get_trending_products(limit)

    # =========================================================
    # AVAILABILITY FILTERING (PRODUCTION SAFE)
    # =========================================================

    @staticmethod
    def _filter_available_products(
        recs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filters out products that have zero available inventory
        across ALL fulfillment locations (stores + warehouses).
        Uses safe two-step queries (no nested PostgREST filters).
        """

        if not recs:
            return []

        product_ids = [r["id"] for r in recs if r.get("id")]
        if not product_ids:
            return []

        # 1) Get all variants for these products
        variant_rows = (
            supabase.table("product_variants")
            .select("id, product_id")
            .in_("product_id", product_ids)
            .execute()
        ).data or []

        if not variant_rows:
            return []

        variant_ids = [v["id"] for v in variant_rows]

        # 2) Check inventory availability
        inv_rows = (
            supabase.table("inventory")
            .select("product_variant_id, quantity_on_hand")
            .in_("product_variant_id", variant_ids)
            .gt("quantity_on_hand", 0)
            .execute()
        ).data or []

        if not inv_rows:
            logger.info("All recommendation candidates filtered due to zero inventory")
            return []

        available_variant_ids = {
            row["product_variant_id"] for row in inv_rows
        }

        available_product_ids = {
            v["product_id"]
            for v in variant_rows
            if v["id"] in available_variant_ids
        }

        return [r for r in recs if r.get("id") in available_product_ids]

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
            logger.exception("RPC recommend_products_by_vector failed")
            return []

    # =========================================================
    # LIVE USER CONTEXT
    # =========================================================

    @staticmethod
    def _compute_live_vector(user_id: str) -> Optional[List[float]]:
        """
        Builds a temporary embedding from recent user activity.
        Used only when precomputed embedding is missing.
        """

        footprints = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .in_("event_type", ["product_view", "product_click", "search"])
            .order("captured_at", desc=True)
            .limit(12)
            .execute()
        )

        if not footprints.data:
            return None

        tokens: List[str] = []
        for row in footprints.data:
            ed = row.get("event_data") or {}
            if ed.get("name"):
                tokens.append(ed["name"])
            if ed.get("category"):
                tokens.append(ed["category"])
            if ed.get("tags"):
                if isinstance(ed["tags"], list):
                    tokens.extend(ed["tags"])
                else:
                    tokens.append(str(ed["tags"]))
            if ed.get("query"):
                tokens.append(ed["query"])

        context_text = " ".join(tokens)[:1800]
        if not context_text:
            return None

        return AIService.generate_embedding(context_text)

    @staticmethod
    def _get_user_context_text(user_id: str) -> str:
        """
        Short human-readable context for agent explanations.
        """

        footprints = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .order("captured_at", desc=True)
            .limit(6)
            .execute()
        )

        parts: List[str] = []
        for row in footprints.data or []:
            ed = row.get("event_data") or {}
            if ed.get("name"):
                parts.append(ed["name"])
            elif ed.get("query"):
                parts.append(ed["query"])

        return " ; ".join(parts)

    # =========================================================
    # AGENT EXPLANATIONS
    # =========================================================

    @staticmethod
    def _attach_explanations(
        recs: List[Dict[str, Any]], user_context: str
    ) -> List[Dict[str, Any]]:

        enriched: List[Dict[str, Any]] = []

        for r in recs:
            reason = None
            try:
                if hasattr(AIService, "explain_recommendation"):
                    reason = AIService.explain_recommendation(
                        product=r,
                        user_context=user_context,
                    )
            except Exception:
                logger.exception("Failed to generate explanation")

            enriched.append({**r, "agent_reason": reason})

        return enriched

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
            if res.data:
                return res.data

            # Fallback: materialize from product IDs
            tv = (
                supabase.table("trending_products_weekly")
                .select("product_id")
                .limit(limit)
                .execute()
            )

            ids = [r["product_id"] for r in (tv.data or [])]
            if not ids:
                return []

            products = (
                supabase.table("products")
                .select("id, name, base_price, product_variants(image_url)")
                .in_("id", ids)
                .execute()
            )

            out = []
            for p in products.data or []:
                img = (
                    p["product_variants"][0]["image_url"]
                    if p.get("product_variants")
                    else None
                )
                out.append({**p, "image_url": img})

            return out

        except Exception:
            logger.exception("Trending products fetch failed")
            return []

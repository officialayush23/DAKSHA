# app/services/recommendation_service.py
import logging
from typing import Optional, List, Dict, Any
from app.database import supabase
from app.services.ai_service import AIService

logger = logging.getLogger("daksha.recommendation")


class RecommendationService:
    @staticmethod
    def get_personalized_recommendations(user_id: Optional[str], limit: int = 8) -> List[Dict[str, Any]]:
        # 1) Precomputed embedding path
        try:
            if user_id:
                emb_row = supabase.table("user_embeddings").select("embedding").eq("user_id", user_id).maybe_single().execute()
                emb = emb_row.data.get("embedding") if emb_row.data else None
                if emb:
                    recs = RecommendationService._rpc_recommend_by_vector(emb, limit)
                    if recs:
                        # attach short explanation for each
                        user_context = RecommendationService._get_user_context_text(user_id)
                        return RecommendationService._attach_explanations(recs, user_context)
            # 2) Live path: compute quickly and search
            if user_id:
                live_emb = RecommendationService._compute_live_vector(user_id)
                if live_emb:
                    recs = RecommendationService._rpc_recommend_by_vector(live_emb, limit)
                    if recs:
                        user_context = RecommendationService._get_user_context_text(user_id)
                        return RecommendationService._attach_explanations(recs, user_context)
            # 3) Fallback trending
            return RecommendationService.get_trending_products(limit)
        except Exception:
            logger.exception("Personalized recs failed")
            return RecommendationService.get_trending_products(limit)

    @staticmethod
    def _rpc_recommend_by_vector(vec: List[float], limit: int):
        try:
            res = supabase.rpc("recommend_products_by_vector", {
                "query_embedding": vec,
                "match_threshold": 0.55,
                "match_count": limit
            }).execute()
            return res.data or []
        except Exception:
            logger.exception("RPC recommend_products_by_vector failed")
            return []

    @staticmethod
    def _compute_live_vector(user_id: str) -> Optional[List[float]]:
        footprints = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .eq("event_type", "view_product")
            .order("captured_at", desc=True)
            .limit(12)
            .execute()
        )
        if not footprints.data:
            return None
        tokens = []
        for h in footprints.data:
            ed = h.get("event_data", {}) or {}
            if ed.get("name"):
                tokens.append(ed["name"])
            if ed.get("category"):
                tokens.append(ed["category"])
            if ed.get("tags"):
                tokens.append(" ".join(ed["tags"]) if isinstance(ed["tags"], list) else ed["tags"])
        context_text = " ".join(tokens)[:1800] or "recent_browsing"
        return AIService.generate_embedding(context_text)

    @staticmethod
    def _get_user_context_text(user_id: str):
        footprints = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .order("captured_at", desc=True)
            .limit(6)
            .execute()
        )
        parts = []
        for f in footprints.data or []:
            ed = f.get("event_data", {}) or {}
            if ed.get("name"):
                parts.append(ed["name"])
            elif ed.get("query"):
                parts.append(ed["query"])
        return " ; ".join(parts)

    @staticmethod
    def _attach_explanations(recs, user_context: str):
        out = []
        # Try to use AIService.explain_recommendation if available
        for r in recs:
            try:
                reason = None
                if hasattr(AIService, "explain_recommendation"):
                    # provide a concise explanation (safe rate-limited call)
                    reason = AIService.explain_recommendation(product=r, user_context=user_context)
                out.append({**r, "agent_reason": reason})
            except Exception:
                out.append({**r, "agent_reason": None})
        return out

    @staticmethod
    def get_trending_products(limit: int = 8):
        try:
            res = supabase.table("trending_products_weekly_cards").select("*").limit(limit).execute()
            if res.data:
                return res.data
            # fallback to trending_products_weekly -> fetch product details
            tv = supabase.table("trending_products_weekly").select("product_id").limit(limit).execute()
            ids = [r["product_id"] for r in (tv.data or [])]
            if not ids:
                return []
            products = supabase.table("products").select("id,name,base_price,product_variants(image_url)").in_("id", ids).execute()
            out = []
            for p in products.data or []:
                img = p.get("product_variants")[0]["image_url"] if p.get("product_variants") else None
                out.append({**p, "image_url": img})
            return out
        except Exception:
            logger.exception("Trending fetch failed")
            return []

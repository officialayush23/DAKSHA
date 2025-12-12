# app/services/embeddings_worker.py
from datetime import datetime
from app.database import supabase
from app.services.ai_service import AIService
import logging

logger = logging.getLogger("daksha.embeddings_worker")


class EmbeddingsWorker:
    @staticmethod
    def fetch_recent_product_context(user_id: str, limit: int = 20):
        res = (
            supabase.table("user_footprints")
            .select("event_data")
            .eq("user_id", user_id)
            .eq("event_type", "view_product")
            .order("captured_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    @staticmethod
    def build_persona_text(footprints):
        parts = []
        for f in footprints:
            ed = f.get("event_data", {}) or {}
            segs = []
            if ed.get("name"):
                segs.append(str(ed["name"]))
            if ed.get("category"):
                segs.append(str(ed["category"]))
            if ed.get("tags"):
                if isinstance(ed["tags"], list):
                    segs.append(" ".join(ed["tags"]))
                else:
                    segs.append(str(ed["tags"]))
            if segs:
                parts.append(" ".join(segs))
        return " ; ".join(parts[:50]) or "recent_browsing"

    @staticmethod
    def compute_and_upsert_user_embedding(user_id: str, source: str = "session_agg"):
        try:
            footprints = EmbeddingsWorker.fetch_recent_product_context(user_id)
            if not footprints:
                logger.info("No footprints for user %s", user_id)
                return None
            persona_text = EmbeddingsWorker.build_persona_text(footprints)
            emb = AIService.generate_embedding(persona_text)
            if not emb:
                logger.error("Empty embedding for user %s", user_id)
                return None
            payload = {
                "user_id": user_id,
                "embedding": emb,
                "source": source,
                "updated_at": datetime.utcnow().isoformat(),
            }
            existing = supabase.table("user_embeddings").select("id").eq("user_id", user_id).maybe_single().execute()
            if existing.data:
                res = supabase.table("user_embeddings").update({"embedding": emb, "source": source, "updated_at": payload["updated_at"]}).eq("user_id", user_id).execute()
            else:
                res = supabase.table("user_embeddings").insert(payload).execute()
            if getattr(res, "error", None):
                logger.error("Upsert user_embeddings error: %s", res.error)
                return None
            logger.info("Upserted embedding for %s", user_id)
            return res.data[0] if res.data else None
        except Exception:
            logger.exception("Embedding compute failure for %s", user_id)
            return None

# app/services/omni_session_service.py

from typing import Optional
from app.database import supabase
import logging

logger = logging.getLogger("daksha.omni")

class OmniSessionService:
    @staticmethod
    def upsert_session(
        channel_type: str,
        channel_id: str,
        user_id: Optional[str],
        chat_session_id: Optional[str],
        active_cart_id: Optional[str],
        context_summary: Optional[str] = None,
    ):
        try:
            # Check existing
            existing = (
                supabase.table("omni_channel_sessions")
                .select("*")
                .eq("channel_type", channel_type)
                .eq("channel_id", channel_id)
                .maybe_single()
                .execute()
            )

            payload = {
                "channel_type": channel_type,
                "channel_id": channel_id,
                "user_id": user_id,
                "chat_session_id": chat_session_id,
                "active_cart_id": active_cart_id,
                "context_summary": context_summary,
            }

            # Update if exists
            if existing and getattr(existing, "data", None):
                supabase.table("omni_channel_sessions").update(payload).eq(
                    "id", existing.data["id"]
                ).execute()
                return existing.data["id"]

            # Insert new
            res = supabase.table("omni_channel_sessions").insert(payload).execute()
            if res and res.data:
                return res.data[0]["id"]
            return None

        except Exception as e:
            logger.error(f"Upsert Session Error: {e}")
            return None

    @staticmethod
    def get_session(channel_type: str, channel_id: str):
        try:
            res = (
                supabase.table("omni_channel_sessions")
                .select("*")
                .eq("channel_type", channel_type)
                .eq("channel_id", channel_id)
                .maybe_single()
                .execute()
            )
            # ✅ FIX: Explicit check to prevent 500 Crash
            if not res:
                return None
            return res.data
        except Exception as e:
            logger.error(f"Get Session Error: {e}")
            return None
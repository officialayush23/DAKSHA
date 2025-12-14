# app/services/omni_session_service.py

from typing import Optional
from app.database import supabase


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

        if existing.data:
            supabase.table("omni_channel_sessions").update(payload).eq(
                "id", existing.data["id"]
            ).execute()
            return existing.data["id"]

        res = supabase.table("omni_channel_sessions").insert(payload).execute()
        return res.data[0]["id"]

    @staticmethod
    def get_session(channel_type: str, channel_id: str):
        res = (
            supabase.table("omni_channel_sessions")
            .select("*")
            .eq("channel_type", channel_type)
            .eq("channel_id", channel_id)
            .maybe_single()
            .execute()
        )
        return res.data

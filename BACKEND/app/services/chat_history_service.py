# app/services/chat_history_service.py
from app.database import supabase
from datetime import datetime
import json
import logging

logger = logging.getLogger("daksha.history")

class ChatHistoryService:
    
    @staticmethod
    def get_or_create_session(user_id: str | None, channel: str, channel_id: str):
        """
        Finds active session or creates new one using your schema:
        (entry_channel, entry_channel_id)
        """
        # 1. Map generic channel string to DB Enum if needed
        # Assuming channel_type_enum values are 'web', 'app', 'kiosk', etc.
        db_channel_enum = channel.split('_')[0] if "_" in channel else channel 

        # 2. Check Omni-Session first (Fast Lookup)
        omni = (
            supabase.table("omni_channel_sessions")
            .select("chat_session_id")
            .eq("channel_type", channel)
            .eq("channel_id", channel_id)
            .maybe_single()
            .execute()
        )

        session_id = omni.data.get("chat_session_id") if omni.data else None

        # 3. Create Session if missing
        if not session_id:
            try:
                # Using YOUR table schema
                new_sess = supabase.table("chat_sessions").insert({
                    "user_id": user_id if user_id != "guest" else None,
                    "entry_channel": db_channel_enum, 
                    "entry_channel_id": channel_id,
                    "summary": "New conversation started",
                    "sentiment_trend": 0.0
                }).execute()
                
                if new_sess.data:
                    session_id = new_sess.data[0]["id"]
                    # Link Omni
                    ChatHistoryService.upsert_omni(channel, channel_id, user_id, session_id)
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                return None

        return session_id

    @staticmethod
    def upsert_omni(channel, channel_id, user_id, session_id):
        # Keeps your omni_channel_sessions table in sync
        payload = {
            "channel_type": channel,
            "channel_id": channel_id,
            "user_id": user_id if user_id != "guest" else None,
            "chat_session_id": session_id,
            "last_active_at": datetime.utcnow().isoformat()
        }
        existing = supabase.table("omni_channel_sessions").select("id").eq("channel_type", channel).eq("channel_id", channel_id).maybe_single().execute()
        if existing.data:
            supabase.table("omni_channel_sessions").update(payload).eq("id", existing.data["id"]).execute()
        else:
            supabase.table("omni_channel_sessions").insert(payload).execute()

    @staticmethod
    def save_message(session_id: str, role: str, content: str, tool_used: str = None, payload: dict = None):
        """
        Writes to your 'chat_messages' table.
        - role -> sender
        - payload -> metadata
        """
        try:
            supabase.table("chat_messages").insert({
                "session_id": session_id,
                "sender": role, # 'user' or 'assistant'
                "content": content,
                "tool_used": tool_used,
                "metadata": payload, # Stores product JSON here!
                "input_modality": "text",
                "detected_language": "en"
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    @staticmethod
    def load_history(session_id: str, limit=6):
        """
        Reads from 'chat_messages' and maps 'sender' back to LangChain 'role'.
        """
        try:
            res = (
                supabase.table("chat_messages")
                .select("sender, content")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            # Map 'sender' -> 'role'
            # Reverse to get chronological order (Oldest -> Newest)
            history = []
            rows = reversed(res.data) if res.data else []
            
            for r in rows:
                role = "user" if r["sender"] == "user" else "assistant"
                history.append({"role": role, "content": r["content"]})
                
            return history
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
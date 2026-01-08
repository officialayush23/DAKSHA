# app/services/chat_history_service.py
from app.core.database import supabase_admin
from datetime import datetime
import json
import logging

logger = logging.getLogger("daksha.history")

class ChatHistoryService:
    
    @staticmethod
    def get_or_create_session(user_id: str | None, channel: str, channel_id: str):
        """
        Finds active session or creates new one using conversation_sessions table.
        Matches DB schema: conversation_sessions (not chat_sessions)
        """
        # 1. DB Enum values: web, mobile, whatsapp, kiosk, voice, admin
        # Use channel directly - no mapping needed
        db_channel_enum = channel 

        # 2. Check for existing active conversation session
        # Look for active session for this user/channel combination
        existing = (
            supabase_admin.table("conversation_sessions")
            .select("id")
            .eq("user_id", user_id if user_id != "guest" else None)
            .eq("started_from", db_channel_enum)
            .eq("status", "active")
            .order("created_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )

        session_id = existing.data.get("id") if existing.data else None

        # 3. Create Session if missing
        if not session_id:
            try:
                # Use conversation_sessions table (matches DB schema)
                # In Supabase v2, insert() already returns data - no need for .select()
                new_sess = supabase_admin.table("conversation_sessions").insert({
                    "user_id": user_id if user_id != "guest" else None,
                    "started_from": db_channel_enum,
                    "summary": "New conversation started",
                    "status": "active",
                    "state": {},
                    "state_version": 1
                }).execute()
                
                if new_sess.data:
                    session_id = new_sess.data[0]["id"]
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                return None

        return session_id

    @staticmethod
    def upsert_omni(channel, channel_id, user_id, session_id):
        """
        Note: omni_channel_sessions table may not exist in the provided schema.
        This method is kept for backward compatibility but may need adjustment.
        """
        # If omni_channel_sessions exists, keep it in sync
        # Otherwise, this is a no-op
        try:
            payload = {
                "channel_type": channel,
                "channel_id": channel_id,
                "user_id": user_id if user_id != "guest" else None,
                "chat_session_id": session_id,  # May need to be conversation_id
                "last_active_at": datetime.utcnow().isoformat()
            }
            existing = supabase_admin.table("omni_channel_sessions").select("id").eq("channel_type", channel).eq("channel_id", channel_id).maybe_single().execute()
            if existing.data:
                supabase_admin.table("omni_channel_sessions").update(payload).eq("id", existing.data["id"]).execute()
            else:
                # In Supabase v2, insert() already returns data - no need for .select()
                supabase_admin.table("omni_channel_sessions").insert(payload).execute()
        except Exception as e:
            # Table may not exist, silently fail
            logger.debug(f"omni_channel_sessions not available: {e}")
            pass

    @staticmethod
    def save_message(session_id: str, role: str, content: str, tool_used: str = None, payload: dict = None):
        """
        Writes to conversation_messages table (matches DB schema).
        - role -> sender ('user', 'agent', 'tool')
        - tool_used -> tool_name
        - payload -> metadata
        Also publishes to Redis for real-time updates.
        """
        try:
            # Map role to sender: 'user' or 'assistant' -> 'user' or 'agent'
            sender = "user" if role == "user" else "agent"
            
            # In Supabase v2, insert() already returns data - no need for .select()
            result = supabase_admin.table("conversation_messages").insert({
                "session_id": session_id,  # References conversation_sessions.id
                "sender": sender,  # 'user', 'agent', or 'tool'
                "content": content,
                "tool_name": tool_used,  # Matches schema field name
                "metadata": payload,  # Stores product JSON here!
            }).execute()
            
            # Publish to Redis for real-time updates (async, non-blocking)
            if result.data:
                try:
                    import asyncio
                    from app.core.database import redis_client
                    import json
                    message_data = {
                        "id": result.data[0]["id"],
                        "sender": sender,
                        "content": content,
                        "tool_name": tool_used,
                        "metadata": payload,
                        "created_at": result.data[0].get("created_at")
                    }
                    # Fire and forget - don't block
                    asyncio.create_task(
                        redis_client.publish(
                            f"chat:{session_id}",
                            json.dumps(message_data)
                        )
                    )
                except Exception as e:
                    logger.debug(f"Redis publish failed (non-critical): {e}")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    @staticmethod
    def load_history(session_id: str, limit=6):
        """
        Reads from conversation_messages and maps 'sender' back to LangChain 'role'.
        """
        try:
            res = (
                supabase_admin.table("conversation_messages")
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
                # Map: 'user' -> 'user', 'agent' or 'tool' -> 'assistant'
                role = "user" if r["sender"] == "user" else "assistant"
                history.append({"role": role, "content": r["content"]})
                
            return history
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
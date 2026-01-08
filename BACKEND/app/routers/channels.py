# app/routers/channels.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from app.core.auth import get_current_user_id
from app.schemas.schemas import ChannelMessage
from app.agents.graph import run_sales_agent
from app.services.chat_history_service import ChatHistoryService
from app.core.database import supabase

router = APIRouter(prefix="/channels", tags=["Omnichannel"])

@router.post("/message")
async def handle_message(
    payload: ChannelMessage,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    # DB Enum values: web, mobile, whatsapp, kiosk, voice, admin
    # Use channel_type directly - no mapping needed
    reply = await run_sales_agent(
        user_id=user_id,
        channel=payload.channel_type,  # Direct enum value
        channel_id=payload.channel_id,
        message=payload.message,
    )

    # Extract conversation_id from reply if available
    # The session_id returned is actually conversation_sessions.id
    conversation_id = None
    if isinstance(reply, dict) and "conversation_id" in reply:
        conversation_id = reply["conversation_id"]
    elif isinstance(reply, dict) and "session_id" in reply:
        conversation_id = reply["session_id"]

    return {
        "reply": reply,
        "conversation_id": conversation_id
    }


@router.get("/conversations")
async def get_conversations(
    user_id: Optional[str] = Depends(get_current_user_id),
    limit: int = 20
):
    """Get user's conversation history"""
    if not user_id:
        return {"conversations": []}
    
    try:
        conversations = (
            supabase.table("conversation_sessions")
            .select("id, started_from, summary, status, created_at, updated_at")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch conversations: {str(e)}")


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    limit: int = 50
):
    """Get messages for a specific conversation"""
    try:
        # Verify conversation belongs to user
        conv = (
            supabase.table("conversation_sessions")
            .select("user_id")
            .eq("id", conversation_id)
            .maybe_single()
            .execute()
        ).data
        
        if not conv:
            raise HTTPException(404, "Conversation not found")
        
        if user_id and conv.get("user_id") != user_id:
            raise HTTPException(403, "Access denied")
        
        messages = (
            supabase.table("conversation_messages")
            .select("id, sender, content, tool_name, metadata, created_at")
            .eq("session_id", conversation_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        
        # Reverse to get chronological order
        messages.reverse()
        
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch messages: {str(e)}")
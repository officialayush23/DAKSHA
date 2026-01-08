# app/services/human_handoff_service.py

from app.core.database import supabase_admin
from typing import Optional, Dict


class HumanHandoffService:
    """
    Single authority for escalating AI → Human.
    """

    @staticmethod
    def trigger(
        *,
        session_id: Optional[str],
        user_id: Optional[str],
        reason: str,
        summary: str,
        metadata: Optional[Dict] = None,
    ):
        """
        Trigger human handoff. Maps session_id to conversation_id.
        Should use propose_handoff RPC when available.
        """
        # session_id should be conversation_sessions.id (matches DB schema)
        conversation_id = session_id
        
        # Verify it's a valid conversation_sessions.id
        if session_id:
            conv = (
                supabase_admin.table("conversation_sessions")
                .select("id")
                .eq("id", session_id)
                .maybe_single()
                .execute()
            ).data
            
            if not conv:
                # If not found, session_id is invalid
                logger.warning(f"Invalid conversation_sessions.id: {session_id}")
                conversation_id = None
        
        # Get context snapshot (recent messages from conversation_messages)
        context_snapshot = {}
        if conversation_id:
            messages = (
                supabase_admin.table("conversation_messages")
                .select("sender, content, created_at, metadata")
                .eq("session_id", conversation_id)  # References conversation_sessions.id
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            ).data or []
            context_snapshot = {
                "recent_messages": messages,
                "metadata": metadata or {},
            }
        
        # Calculate confidence from metadata if available
        confidence_score = metadata.get("confidence", 0.5) if metadata else 0.5
        
        # Use RPC if available, otherwise direct insert (for now)
        try:
            from app.core.rpc import RPCService
            
            # Get agent_run_id if available from metadata
            agent_run_id = metadata.get("agent_run_id") if metadata else None
            
            if agent_run_id:
                RPCService.propose_handoff(
                    agent_run_id=agent_run_id,
                    reason=reason,
                    confidence=confidence_score,
                    context=context_snapshot,
                )
                # RPC handles the insert, so we return success
                return {"status": "handoff_proposed", "reason": reason}
        except Exception:
            # Fallback to direct insert if RPC not available
            pass
        
        # Direct insert (fallback)
        payload = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "reason": reason,  # Should match handoff_reason_enum
            "confidence_score": confidence_score,
            "context_snapshot": context_snapshot,
            "status": "pending",  # Should match handoff_status_enum
        }

        # In Supabase v2, insert() already returns data - no need for .select()
        handoff = (
            supabase_admin.table("human_handoffs")
            .insert(payload)
            .execute()
        ).data[0]

        # Auto-create support ticket if user context exists
        if user_id:
            # In Supabase v2, insert() already returns data - no need for .select()
            supabase_admin.table("support_tickets").insert(
                {
                    "user_id": user_id,
                    "ticket_type": "general",  # Default type
                    "status": "open",  # Use 'status' not 'ticket_status'
                    "subject": reason,
                    "description": summary,
                }
            ).execute()

        return handoff

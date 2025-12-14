# app/services/human_handoff_service.py

from app.database import supabase
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
        payload = {
            "session_id": session_id,
            "reason": reason,
            "handoff_summary": summary,
            "status": "pending",
        }

        handoff = (
            supabase.table("human_handoffs")
            .insert(payload)
            .execute()
        ).data[0]

        # Auto-create support ticket if user context exists
        if user_id:
            supabase.table("support_tickets").insert(
                {
                    "user_id": user_id,
                    "ticket_status": "open",
                    "issue_summary": reason,
                    "conversation_summary": summary,
                    "resolved_by": None,
                }
            ).execute()

        return handoff

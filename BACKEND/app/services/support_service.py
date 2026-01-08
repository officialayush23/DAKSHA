# app/services/support_service.py

from app.core.database import supabase_admin
from app.core.redis_bus import EventBus


class SupportService:
    @staticmethod
    async def create_ticket(
        user_id: str,
        issue_summary: str,
        conversation_summary: str,
        sentiment_score: float = 0.5,
        order_id: str | None = None,
        ticket_type: str = "general",
        priority: str = "medium",
    ) -> dict:
        """
        Create support ticket with correct schema fields.
        Uses 'status' not 'ticket_status', 'subject' not 'issue_summary'.
        """
        # In Supabase v2, insert() already returns data - no need for .select()
        res = (
            supabase_admin.table("support_tickets")
            .insert(
                {
                    "user_id": user_id,
                    "order_id": order_id,
                    "ticket_type": ticket_type,  # order_issue, payment_issue, etc.
                    "status": "open",  # Use 'status' not 'ticket_status'
                    "subject": issue_summary,  # Use 'subject' not 'issue_summary'
                    "description": conversation_summary,  # Use 'description' not 'conversation_summary'
                    "priority": priority,  # low, medium, high, urgent
                }
            )
            .execute()
        )
        ticket = res.data[0]
        await EventBus.notify_support_dashboard("new_ticket", ticket)
        return ticket

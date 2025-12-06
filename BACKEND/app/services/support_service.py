from app.database import supabase
from app.core.redis_bus import EventBus


class SupportService:
    @staticmethod
    async def create_ticket(
        user_id: str,
        issue: str,
        summary: str,
        sentiment: float,
        order_id: str | None = None,
    ) -> dict:
        res = (
            supabase.table("support_tickets")
            .insert(
                {
                    "user_id": user_id,
                    "order_id": order_id,
                    "issue_summary": issue,
                    "conversation_summary": summary,
                    "sentiment_score": sentiment,
                    "ticket_status": "open",
                }
            )
            .execute()
        )
        ticket = res.data[0]
        await EventBus.notify_support_dashboard("new_ticket", ticket)
        return ticket

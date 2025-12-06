from langchain.tools import tool
from app.services.support_service import SupportService


@tool
async def create_support_ticket_tool(
    user_id: str,
    issue_summary: str,
    conversation_summary: str,
    sentiment_score: float,
) -> str:
    """
    Create a support ticket and push it to the dashboard.
    """
    ticket = await SupportService.create_ticket(
        user_id, issue_summary, conversation_summary, sentiment_score
    )
    return f"Created support ticket {ticket['id']} with status {ticket['ticket_status']}"

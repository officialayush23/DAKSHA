from langchain.tools import tool
from app.services.loyalty_service import LoyaltyService

@tool
def check_loyalty_status_tool(user_id: str):
    """
    Checks the user's loyalty points balance and available rewards.
    Use this when user asks "How many points do I have?" or "Any rewards?"
    """
    return LoyaltyService.get_loyalty_summary(user_id)
from langchain.tools import tool
from app.services.recommendation_service import RecommendationService

@tool
def get_personalized_recommendations_tool(user_id: str):
    """
    Suggests products based on the user's browsing history (footprints).
    Use this when the user asks "What do you suggest?" or "Show me something I'd like."
    """
    return RecommendationService.get_personalized_recommendations(user_id)

@tool
def get_active_promotions_tool(user_id: str):
    """
    Fetches active ad campaigns or special sales events.
    """
    return RecommendationService.get_active_campaigns(user_id)
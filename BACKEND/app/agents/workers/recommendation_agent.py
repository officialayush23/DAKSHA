# app/agents/workers/recommendation_agent.py
from app.agents.base import BaseWorkerAgent
from app.services.recommendation_service import RecommendationService

class RecommendationAgent(BaseWorkerAgent):
    name = "recommendation_agent"

    def run(self, user_id: str, limit: int = 5):
        items = RecommendationService.get_personalized_recommendations(user_id, limit)
        self.log_run(user_id, "personalized_recommendations", f"{len(items)} items")
        return items

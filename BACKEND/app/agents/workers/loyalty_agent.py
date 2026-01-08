# app/agents/workers/loyalty_agent.py

from app.agents.base import BaseWorkerAgent
from app.services.loyalty_service import LoyaltyService
from app.services.promotion_service import PromotionService

class LoyaltyAgent(BaseWorkerAgent):
    name = "loyalty_agent"

    def run(self, user_id: str):
        loyalty = LoyaltyService.get_loyalty_summary(user_id)
        promos = PromotionService.get_active_promotions(limit=3)

        self.log_run(user_id, "loyalty_check", "ok")
        return {
            "loyalty": loyalty,
            "promotions": promos,
        }

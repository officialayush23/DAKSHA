# app/agents/workers/payment_agent.py
from app.agents.base import BaseWorkerAgent
from app.services.commerce_service import CommerceService

class PaymentAgent(BaseWorkerAgent):
    name = "payment_agent"

    def run(self, user_id: str, order_id: str):
        # Payment creation is intentionally NOT RPC-only yet (as you noted)
        result = CommerceService.create_payment_intent(order_id)
        self.log_run(user_id, f"payment_intent:{order_id}", "created")
        return result
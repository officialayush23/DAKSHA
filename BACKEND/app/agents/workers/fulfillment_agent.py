# app/agents/workers/fulfillment_agent.py

from app.agents.base import BaseWorkerAgent
from app.core.database import supabase
from app.services.human_handoff_service import HumanHandoffService

class FulfillmentAgent(BaseWorkerAgent):
    name = "fulfillment_agent"

    def run(self, *, order_id: str, user_id: str | None):
        order = (
            supabase.table("orders")
            .select("id, status")
            .eq("id", order_id)
            .maybe_single()
            .execute()
        ).data

        if not order:
            HumanHandoffService.trigger(
                session_id=None,
                user_id=user_id,
                reason="order_not_found",
                summary=f"Order {order_id} not found during fulfillment"
            )
            return {"status": "escalated"}

        # Fulfillment itself is done by ops / RPCs
        self.log_run(
            user_id,
            f"fulfillment_check:{order_id}",
            f"status={order['status']}"
        )

        return {
            "status": "queued_for_ops",
            "order_status": order["status"],
        }

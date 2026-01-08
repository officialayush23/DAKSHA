
# app/agents/workers/support_agent.py
from app.agents.base import BaseWorkerAgent
from app.services.human_handoff_service import HumanHandoffService

class SupportAgent(BaseWorkerAgent):
    name = "support_agent"

    def run(self, user_id: str, reason: str, summary: str):
        HumanHandoffService.trigger(
            session_id=None,
            user_id=user_id,
            reason=reason,
            summary=summary
        )
        self.log_run(user_id, "handoff", reason)
        return {"status": "escalated"}

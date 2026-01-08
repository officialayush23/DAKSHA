# app/agents/budget.py

from app.core.database import supabase
from datetime import datetime

class AgentBudgetEnforcer:
    @staticmethod
    def track(agent_name: str, session_id: str, confidence: float):
        """
        Soft enforcement.
        Hard enforcement can be added later.
        """
        try:
            # In Supabase v2, insert() already returns data - no need for .select()
            supabase.table("agent_usage").insert(
                {
                    "agent_name": agent_name,
                    "session_id": session_id,
                    "confidence": confidence,
                    "created_at": datetime.utcnow(),
                }
            ).execute()
        except Exception:
            pass

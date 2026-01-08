# app/agents/base.py
from abc import ABC, abstractmethod
from app.core.database import supabase

class BaseWorkerAgent(ABC):
    name: str

    @abstractmethod
    def run(self, **kwargs):
        pass

    def log_run(self, user_id: str | None, input_summary: str, output_summary: str):
        try:
            # In Supabase v2, insert() already returns data - no need for .select()
            supabase.table("agent_runs").insert({
                "agent_name": self.name,
                "user_id": user_id,
                "input_summary": input_summary,
                "output_summary": output_summary,
                "success": True,
            }).execute()
        except:
            pass

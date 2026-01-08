# app/agents/confidence.py

from langchain_core.messages import AIMessage, ToolMessage

class ConfidenceScorer:
    @staticmethod
    def score(messages: list) -> float:
        score = 1.0

        for m in messages:
            if isinstance(m, ToolMessage):
                if "error" in (m.content or "").lower():
                    score -= 0.4

            if isinstance(m, AIMessage):
                text = (m.content or "").lower()
                if any(x in text for x in [
                    "not sure",
                    "might be wrong",
                    "can't help",
                    "uncertain"
                ]):
                    score -= 0.3

        return max(score, 0.0)

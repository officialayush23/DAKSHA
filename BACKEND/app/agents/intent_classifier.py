# app/agents/intent_classifier.py

from app.services.ai_service import AIService

INTENT_PROMPT = """
Classify the user's intent into ONE of these:
- discovery
- recommendation
- inventory
- cart
- checkout
- order_tracking
- support
- human_handoff

Return ONLY the intent key.
"""

class IntentClassifier:
    @staticmethod
    async def classify(message: str) -> str:
        llm = AIService.get_intent_llm()
        res = await llm.ainvoke(INTENT_PROMPT + "\nUser: " + message)
        return res.content.strip().lower()

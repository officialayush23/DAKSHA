# app/services/ai_service.py
# app/services/ai_service.py

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential


class AIService:
    # ---------------------------
    # EXISTING (unchanged)
    # ---------------------------

    @staticmethod
    def get_embeddings():
        return GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60))
    def generate_embedding(text: str) -> list[float]:
        model = AIService.get_embeddings()
        return model.embed_query(text)

    @staticmethod
    def get_llm():
        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
            max_retries=6,
            request_timeout=60,
        )

    @staticmethod
    async def describe_image(image_url: str) -> str:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY
        )

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Describe this fashion product in high detail for a search engine. "
                        "Include color, material, pattern, fit, style, and key features."
                    )
                },
                {"type": "image_url", "image_url": image_url},
            ]
        )

        res = await llm.ainvoke([message])
        return res.content

    # ---------------------------
    # NEW (Phase 6 – additive)
    # ---------------------------

    @staticmethod
    def get_intent_llm():
        """
        Lightweight, cheap router model (DeepSeek).
        """
        return ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            temperature=0,
            max_tokens=20,
        )

    @staticmethod
    def get_reasoning_llm():
        """
        Strong reasoning LLM (Gemini).
        """
        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
        )

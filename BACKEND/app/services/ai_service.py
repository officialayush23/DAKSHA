# app/services/ai_service.py

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from app.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

class AIService:
    @staticmethod
    def get_embeddings():
        return GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60)) # Increased patience
    def generate_embedding(text: str) -> list[float]:
        model = AIService.get_embeddings()
        return model.embed_query(text)

    @staticmethod
    def get_llm():
        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
            max_retries=6, # Built-in retry
            request_timeout=60, # Allow longer waits
        )
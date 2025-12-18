from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
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
        """
        Uses Gemini Vision to convert an Image -> Rich Text Description.
        This allows us to 'embed' images using our existing text embedding model.
        """
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", # Vision capable model
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Describe this fashion product in high detail for a search engine. Include color, material, pattern, fit, style (casual/formal), and key features. Return ONLY the description, no filler."},
                {"type": "image_url", "image_url": image_url},
            ]
        )
        
        res = await llm.ainvoke([message])
        return res.content
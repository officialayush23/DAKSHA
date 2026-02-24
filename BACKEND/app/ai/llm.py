# app/ai/llm.py
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        max_output_tokens=1024,
        api_key=settings.GEMINI_API_KEY
    )
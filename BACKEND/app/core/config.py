# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Commerce Platform"

    # Database
    DATABASE_URL: str
    NOMIC_API_KEY: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str  
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    EMBEDDING_PROVIDER: str = "nomic"
    NOMIC_TEXT_MODEL: str = "nomic-embed-text-v1.5"
    NOMIC_VISION_MODEL: str = "nomic-embed-vision-v1.5"
    NOMIC_MATRYOSHKA_DIM: int = 768
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "daksha"

    # AI
    GROQ_API_KEY: str = ""
    TELEGRAM_TOKEN: str = ""

    # Email (Resend)
    RESEND_API_KEY: str = ""

    # Maps
    MAP_BOX_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    # Vertex AI / Gemini
    GEMINI_VERTEX_API_KEY: str = ""
    VERTEX_AI_LOCATION: str = "asia-south1"
    VERTEX_API_KEY: str = ""

    # LangGraph checkpointer (session pooler — supports prepared statements)
    LANGGRAPH_DB_URL: str = ""

    # Infra
    REDIS_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"   # 🔑 DO NOT REMOVE


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

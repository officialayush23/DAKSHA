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
    SMTP_HOST:str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str

    RENDER_API_KEY: str


    EMBEDDING_PROVIDER: str
    NOMIC_TEXT_MODEL: str
    NOMIC_VISION_MODEL: str
    NOMIC_MATRYOSHKA_DIM: int
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str
    # 🔑 THIS WAS MISSING

    # AI
    GEMINI_API_KEY: str
    GROQ_API_KEY: str
    TELEGRAM_TOKEN: str

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

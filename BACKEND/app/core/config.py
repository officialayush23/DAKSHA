# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Commerce Platform"

    # Database
    DATABASE_URL: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str   # 🔑 THIS WAS MISSING

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

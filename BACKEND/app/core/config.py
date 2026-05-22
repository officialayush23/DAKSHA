# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "DAKSHA Agentic Commerce Platform"

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str            # transaction pooler (port 6543)
    LANGGRAPH_DB_URL: str = ""   # session pooler (port 5432) — for LangGraph checkpointer

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # ── AI / Gemini (AQ. prefix keys) ─────────────────────────────────────────
    GEMINI_VERTEX_API_KEY: str = ""
    VERTEX_API_KEY: str = ""
    VERTEX_AI_LOCATION: str = "asia-south1"

    # ── Groq ──────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""

    # ── Maps ──────────────────────────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""
    MAP_BOX_API_KEY: str = ""

    # ── Embeddings (Nomic) ────────────────────────────────────────────────────
    NOMIC_API_KEY: str
    EMBEDDING_PROVIDER: str = "nomic"
    NOMIC_TEXT_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"
    NOMIC_VISION_MODEL: str = "nomic-ai/nomic-embed-vision-v1.5"
    NOMIC_MATRYOSHKA_DIM: int = 768

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    RESEND_API_KEY: str = ""

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str

    # ── Misc ──────────────────────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = ""
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "daksha"

    # ── CORS — comma-separated list of allowed frontend origins ───────────────
    # Example: https://daksha.vercel.app,https://www.daksha.com
    FRONTEND_URLS: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"   # ignore any extra env vars silently


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

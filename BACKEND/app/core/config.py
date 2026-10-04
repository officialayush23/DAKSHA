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

    # ── AI / Gemini ───────────────────────────────────────────────────────────
    # Option A — Vertex AI (production, no rate limits)
    GOOGLE_CLOUD_PROJECT: str = ""            # e.g. "creativedirector-494221"
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    # Paste the entire service-account JSON as a single env var on Render.
    # The app writes it to /tmp at startup so google-auth ADC picks it up.
    GOOGLE_APPLICATION_CREDENTIALS_JSON: str = ""

    # Option B — Google AI Studio API key (AQ. prefix, dev/fallback only)
    GEMINI_VERTEX_API_KEY: str = ""
    VERTEX_API_KEY: str = ""
    VERTEX_AI_LOCATION: str = "us-central1"

    # ── Model gateway (app/agentic/core/llm.py) ──────────────────────────────
    LLM_PROVIDER: str = "gemini"            # primary: gemini | bedrock
    LLM_PROVIDER_ORDER: str = ""            # e.g. "gemini,bedrock" (overrides LLM_PROVIDER)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_THINKING_LEVEL: str = "low"
    GEMINI_FALLBACK_MODELS: str = "gemini-3.5-flash-lite,gemini-3-flash-preview,gemini-2.5-flash"
    AWS_API_KEY_BEDROCK_FOR_XAI: str = ""   # Bedrock API key (ABSK...)
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "us.xai.grok-4.7"

    # ── Orchestration ────────────────────────────────────────────────────────
    DAKSHA_DOMAIN: str = "commerce"         # which domain pack the engine loads
    PROACTIVE_ENABLED: bool = True          # in-app scheduler for follow-ups
    PROACTIVE_INTERVAL_MIN: int = 60
    KIOSK_TOKEN_SECRET: str = ""            # defaults to SUPABASE_JWT_SECRET
    KIOSK_TOKEN_TTL_MIN: int = 30
    KIOSK_OTP_REQUIRED: bool = True

    # ── Groq ──────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""

    # ── Maps ──────────────────────────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""
    MAP_BOX_API_KEY: str = ""     # secret token (sk.) - server side only
    MAPBOX_TOKEN: str = ""        # public token (pk.)

    # ── Embeddings (Nomic) ────────────────────────────────────────────────────
    NOMIC_API_KEY: str = ""
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
    REDIS_URL: str = ""          # optional; in-process fallback when empty/unreachable
    CELERY_ENABLED: bool = False   # use Celery workers only if you run them

    # ── Misc ──────────────────────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = ""
    WEBHOOK_SECRET: str = ""        # courier webhook shared secret (X-Webhook-Secret)
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

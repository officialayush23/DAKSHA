# app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str          # anon key (frontend)
    SUPABASE_SERVICE_ROLE_KEY: str   # backend service (bypasses RLS)
    SUPABASE_JWT_SECRET: str

    REDIS_URL: str
    DEEPSEEK_API_KEY: str | None = None

    GOOGLE_API_KEY: str
    # LLM_MODEL: str = "gemini-2.5-flash"
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"

    class Config:
        env_file = ".env"


settings = Settings()
print("SUPABASE_URL:", settings.SUPABASE_URL)
print("SERVICE ROLE KEY PREFIX:", settings.SUPABASE_SERVICE_ROLE_KEY[:10])
print("ANON KEY PREFIX:", settings.SUPABASE_ANON_KEY[:10])

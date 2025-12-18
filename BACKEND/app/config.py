# app/config.py

# from pydantic_settings import BaseSettings


# class Settings(BaseSettings):
#     SUPABASE_URL: str
#     SUPABASE_KEY: str              # optional anon key (frontend)
#     SUPABASE_SERVICE_ROLE_KEY: str # backend service
#     SUPABASE_JWT_SECRET: str

#     REDIS_URL: str

#     GOOGLE_API_KEY: str
#     # LLM_MODEL: str = "gemini-2.5-flash"
#     LLM_MODEL: str = "gemini-2.5-flash"
#     EMBEDDING_MODEL: str = "models/text-embedding-004"

#     class Config:
#         env_file = ".env"


# settings = Settings()
# print("SUPABASE_URL:", settings.SUPABASE_URL)
# print("SERVICE ROLE KEY PREFIX:", settings.SUPABASE_SERVICE_ROLE_KEY[:10])
# print("ANON KEY PREFIX:", settings.SUPABASE_KEY[:10])


from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str              # optional anon key (frontend)
    SUPABASE_SERVICE_ROLE_KEY: str # backend service
    SUPABASE_JWT_SECRET: str

    # Redis
    REDIS_URL: str

    # AI Models
    GOOGLE_API_KEY: str
    # LLM_MODEL: str = "gemini-2.5-flash"
    LLM_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"

    # 👇 ADDED: Groq API Key for the Router
    GROQ_API_KEY: str

    class Config:
        env_file = ".env"
        # This prevents crashes if your .env has extra variables not listed here
        extra = "ignore" 

settings = Settings()

# Debug prints (Optional - remove in production)
print("SUPABASE_URL:", settings.SUPABASE_URL)
print("SERVICE ROLE KEY PREFIX:", settings.SUPABASE_SERVICE_ROLE_KEY[:10])
print("ANON KEY PREFIX:", settings.SUPABASE_KEY[:10])

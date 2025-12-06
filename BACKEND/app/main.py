from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, commerce, support, analytics, realtime, channels, profile, feedback

app = FastAPI(
    title="Daksha Retail Engine",
    version="v8.0-Production",
    description="Service-Oriented, Google-Native, Real-Time Retail Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(commerce.router)
app.include_router(support.router)
app.include_router(analytics.router)
app.include_router(realtime.router)
app.include_router(channels.router)
app.include_router(profile.router)
app.include_router(feedback.router)

@app.get("/")
def health():
    return {"status": "operational", "ai": "gemini-1.5", "db": "supabase", "cache": "redis"}
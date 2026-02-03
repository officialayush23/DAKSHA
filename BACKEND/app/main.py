# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    admin,
    user,
    recommendation,
    chat,
    admin_chat,
)

app = FastAPI(title="Agentic Commerce Platform")

# ✅ CORS — REQUIRED FOR SUPABASE + FRONTEND
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite
        "http://localhost:3000",   # React alt
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(user.router)
app.include_router(recommendation.router)
app.include_router(chat.router)
app.include_router(admin_chat.router)

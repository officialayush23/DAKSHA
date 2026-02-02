# app/main.py
from fastapi import FastAPI
from app.api.routers import (
    admin,user,recommendation,
)

app = FastAPI(title="Agentic Commerce Platform")

app.include_router(admin.router)
app.include_router(user.router)
app.include_router(recommendation.router)

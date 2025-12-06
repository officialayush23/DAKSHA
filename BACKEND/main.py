from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    users,
    profile,
    catalog,
    analytics,
    cart,
    orders,
    payments,
    inventory,
    feedback,
    support,
    realtime,
    channels,
)

app = FastAPI(
    title="Daksha Retail Engine",
    version="Production-v1",
    description="Multi-Agent Retail Backend with Gemini 1.5, Supabase & Redis",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(catalog.router)
app.include_router(analytics.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(inventory.router)
app.include_router(feedback.router)
app.include_router(support.router)
app.include_router(realtime.router)
app.include_router(channels.router)


@app.get("/")
def health():
    return {"status": "operational", "ai": "gemini-flash", "realtime": "redis"}

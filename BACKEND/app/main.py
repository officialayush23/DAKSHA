# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

from app.services.session_cleanup import expire_sessions
from app.core.database import SessionLocal
from app.core.config import settings
from app.api.routers import (
    admin_global,
    admin_user,
    user,
    kiosk,
    cart,
    chat,
    orders,
    session,
    support,
    products,
    checkout,
    notification,
    coupons,
    stores,
    user_preferences,
    loyalty,
    fulfillment,
    recommendation,
)
from app.api.routers.websocket_handoff import router as ws_handoff_router
from app.api.routers.agent_runs_admin import router as agent_runs_admin_router
from app.api.routers.delivery_webhook import router as delivery_webhook_router

app = FastAPI(title="DAKSHA — Agentic Commerce Platform")

# ── Health check (used by Render) ────────────────────────────────────────────
@app.get("/health", tags=["meta"])
def health():
    return JSONResponse({"status": "ok"})

# ── Session TTL cleanup loop ──────────────────────────────────────────────────
async def session_cleanup_loop():
    while True:
        db = SessionLocal()
        try:
            expire_sessions(db)
        finally:
            db.close()
        await asyncio.sleep(60 * 60)   # every 1 hour

@app.on_event("startup")
async def startup_tasks():
    asyncio.create_task(session_cleanup_loop())

# ── CORS ─────────────────────────────────────────────────────────────────────
# FRONTEND_URLS is a comma-separated list set in Render env vars.
# Falls back to localhost for local dev.
_raw_origins = getattr(settings, "FRONTEND_URLS", "") or ""
_extra = [o.strip() for o in _raw_origins.split(",") if o.strip()]

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
] + _extra

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(admin_global.router)
app.include_router(fulfillment.router)
app.include_router(admin_user.router)
app.include_router(user_preferences.router)
app.include_router(user.router)
app.include_router(kiosk.router)
app.include_router(chat.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(recommendation.router)
app.include_router(session.router)
app.include_router(support.router)
app.include_router(loyalty.router)
app.include_router(checkout.router)
app.include_router(coupons.router)
app.include_router(notification.router)
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(ws_handoff_router)        # WebSocket human handoff
app.include_router(agent_runs_admin_router)  # Admin agent run traces
app.include_router(delivery_webhook_router)  # Courier webhook + delivery tracking

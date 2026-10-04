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
from app.api.routers.agentic_admin import router as agentic_admin_router
from app.api.routers.telegram_webhook import router as telegram_router

app = FastAPI(title="DAKSHA — Agentic Commerce Platform")

# ── Health check (used by Render) ────────────────────────────────────────────
@app.get("/health", tags=["meta"])
def health():
    return JSONResponse({"status": "ok"})

# ── Background loops (no Celery/Redis required) ───────────────────────────────
async def session_cleanup_loop():
    while True:
        db = SessionLocal()
        try:
            expire_sessions(db)
        except Exception as e:
            print(f"[SESSION CLEANUP] {e}")
        finally:
            db.close()
        await asyncio.sleep(60 * 60)   # every 1 hour


async def proactive_loop():
    """Release expired stock holds every 5 min; run proactive follow-ups every PROACTIVE_INTERVAL_MIN."""
    from app.agentic.commerce.proactive import release_expired_holds, scan_and_act
    tick = 0
    await asyncio.sleep(30)
    while True:
        try:
            await asyncio.to_thread(release_expired_holds)
            if settings.PROACTIVE_ENABLED and tick % max(1, settings.PROACTIVE_INTERVAL_MIN // 5) == 0:
                res = await scan_and_act()
                print(f"[PROACTIVE] {res}")
        except Exception as e:
            print(f"[PROACTIVE] {e}")
        tick += 1
        await asyncio.sleep(5 * 60)


@app.on_event("startup")
async def startup_tasks():
    from app.api.routers.websocket_handoff import manager
    manager.loop = asyncio.get_running_loop()
    asyncio.create_task(session_cleanup_loop())
    asyncio.create_task(proactive_loop())

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
app.include_router(agentic_admin_router)     # Approvals, per-agent memory, proactive runs, graph
app.include_router(telegram_router)          # Telegram channel + account linking

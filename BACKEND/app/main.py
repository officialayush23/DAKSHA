# app/main.py
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.services.session_cleanup import expire_sessions
from app.core.database import SessionLocal
from app.api.routers import (
    admin,
    user,
    recommendation,
    chat,
    admin_chat,
    kiosk,
    payment,
    telegram,
    cart,
    checkout,
    orders,
    session,
    support,
    admin_delivery,
    products,
    loyalty,admin_kiosk
)

app = FastAPI(title="Agentic Commerce Platform")

# ---------- SESSION TTL CLEANUP ----------
async def session_cleanup_loop():
    while True:
        db = SessionLocal()
        try:
            expire_sessions(db)
        finally:
            db.close()
        await asyncio.sleep(60 * 60)  # every 1 hour

@app.on_event("startup")
async def startup_tasks():
    asyncio.create_task(session_cleanup_loop())

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- ROUTERS ----------
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(recommendation.router)
app.include_router(chat.router)
app.include_router(admin_chat.router)
app.include_router(kiosk.router)
app.include_router(telegram.router)
app.include_router(payment.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(session.router)
app.include_router(support.router)
app.include_router(admin_delivery.router)
app.include_router(loyalty.router)
app.include_router(products.router)
app.include_router(admin_kiosk.router)

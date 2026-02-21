# app/main.py
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.services.session_cleanup import expire_sessions
from app.core.database import SessionLocal
from app.api.routers import (
    admin_global,
    admin_user,
    user,
    kiosk,
    cart,
    orders,
    session,
    support,
    products,
    loyalty,
    support,
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
app.include_router(admin_global.router)
app.include_router(admin_user.router)
app.include_router(user.router)
app.include_router(kiosk.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(session.router)
app.include_router(support.router)
app.include_router(support.router)
app.include_router(loyalty.router)
app.include_router(products.router)


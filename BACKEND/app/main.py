# src/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.workers.reservation_cleanup import reservation_cleanup_loop

from app.routers import (
    auth, users, profile,analytics, cart, orders, payments,
    inventory, feedback, support, realtime, channels, home,
    omni, fulfillment, recommendations, commerce, notifications,
    catalog_readonly,catalog,
    # Admin
    admin_catalog, admin_inventory, admin_support, admin_promotions,
    admin_rbac, admin_warehouse_inventory, admin_fulfillment,
     admin_inventory_onboarding,admin_knowledge, 
    kiosk,dummy_payment,dev_auth
)

app = FastAPI(
    title="Daksha Retail API",
    version="Production-v1",
    description="Service-Oriented AI Retail Backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- USER FACING ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(catalog.router)
app.include_router(catalog_readonly.router)
app.include_router(analytics.router)
app.include_router(home.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(inventory.router)
app.include_router(feedback.router)
app.include_router(support.router)
app.include_router(realtime.router)
app.include_router(channels.router)
app.include_router(omni.router)
app.include_router(fulfillment.router)
app.include_router(recommendations.router)
app.include_router(dev_auth.router)
app.include_router(commerce.router)
app.include_router(notifications.router)
app.include_router(dummy_payment.router)

# --- ADMIN ---
app.include_router(admin_catalog.router)
app.include_router(admin_inventory.router)
app.include_router(admin_inventory_onboarding.router)
app.include_router(admin_support.router)
app.include_router(admin_promotions.router)
app.include_router(admin_rbac.router)
app.include_router(admin_fulfillment.router)
app.include_router(admin_knowledge.router)
app.include_router(kiosk.router)

# ✅ WAREHOUSE ROUTERS (Distinct)
app.include_router(admin_warehouse_inventory.router)
app.include_router(admin_warehouse_inventory.router_outbound)
app.include_router(admin_warehouse_inventory.router_dashboard)

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(reservation_cleanup_loop())

@app.get("/")
def health():
    return {"status": "operational", "multi_agent": True}
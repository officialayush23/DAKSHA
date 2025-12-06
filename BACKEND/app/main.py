from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Remove OAuth imports
from app.routers import (
    auth, users, profile, catalog, analytics, 
    cart, orders, payments, inventory, feedback, 
    support, realtime, channels,
    admin_catalog, admin_inventory, admin_support,notifications,admin_promotions,omni,
)

app = FastAPI(
    title="Daksha Retail API",
    version="Production-v1",
    description="Service-Oriented AI Retail Backend",
    # REMOVED: swagger_ui_init_oauth (Not needed for Bearer auth)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All Routers
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
app.include_router(admin_catalog.router)
app.include_router(admin_inventory.router)
app.include_router(admin_support.router)
app.include_router(notifications.router)
app.include_router(admin_promotions.router)
app.include_router(omni.router)




@app.get("/")
def health():
    return {"status": "operational", "auth": "jwt-bearer"}
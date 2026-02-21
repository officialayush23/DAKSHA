# app/api/routers/admin_global.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.deps import get_db, get_current_admin
from app.schemas.schemas import *
from app.services.admin_global_service import *

router = APIRouter(
    prefix="/admin/global",
    tags=["Admin – Global"]
)

# =========================================================
# PRODUCTS
# =========================================================

@router.post("/products")
def create_product_api(
    payload: ProductCreate,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return create_product(db, payload, admin.id, reason)


@router.get("/products")
def list_products_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_products(db)

@router.get("/products/{product_id}")
def get_product_api(
    product_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return get_product(db, product_id)

@router.delete("/products/{product_id}")
def delete_product_api(
    product_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return delete_product(db, product_id, admin,reason)

# =========================================================
# VARIANTS + EMBEDDINGS
# =========================================================

@router.post("/variants")
def create_variant_api(
    payload: VariantCreate,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return create_variant(db, payload, admin,reason)

@router.get("/variants")
def list_variants_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_variants(db)

@router.get("/variants/{variant_id}")
def get_variant_api(
    variant_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return get_variant(db, variant_id)

@router.put("/variants/{variant_id}")
def update_variant_api(
    variant_id: UUID,
    
    payload: VariantUpdate,
    reason: str = Query(...),
    
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return update_variant(db, variant_id, payload, admin,reason)

@router.delete("/variants/{variant_id}")
def delete_variant_api(
    variant_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return delete_variant(db, variant_id, admin,reason)

# =========================================================
# PRODUCT IMAGES + IMAGE EMBEDDINGS
# =========================================================

@router.post("/variants/{variant_id}/images")
def add_product_image_api(
    variant_id: UUID,
    image_url: str,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return add_product_image(db, variant_id, image_url, admin,reason)

# =========================================================
# INVENTORY (GLOBAL + STORE)
# =========================================================

@router.post("/inventory/global")
def assign_global_inventory_api(
    payload: AssignGlobalInventory,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return assign_global_inventory(db, payload, admin.id,reason)

@router.post("/inventory/store")
def assign_store_inventory_api(
    payload: AssignStoreInventory,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return assign_store_inventory(db, payload, admin.id,reason)

@router.get("/inventory/global")
def list_global_inventory_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_global_inventory(db)

@router.get("/inventory/store")
def list_store_inventory_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_store_inventory(db)

# =========================================================
# STORES + GEO
# =========================================================

@router.post("/stores")
def create_store_api(
    payload: StoreCreate,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return create_store(db, payload, admin,reason)

@router.get("/stores")
def list_stores_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_stores(db)

# =========================================================
# KIOSKS
# =========================================================

@router.post("/kiosks")
def create_kiosk_api(
    payload: KioskCreate,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return create_kiosk(db, payload, admin,reason)

@router.get("/kiosks")
def list_kiosks_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_kiosks(db)

# =========================================================
# PICKUPS (RESCHEDULE + STATUS)
# =========================================================

@router.get("/pickups")
def list_pickups_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_pickups(db)

@router.patch("/pickups/{pickup_id}")
def update_pickup_api(
    pickup_id: UUID,
    payload: PickupStatusUpdate,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return update_pickup(
        db,
        pickup_id,
        status=payload.status,
        scheduled_time=payload.scheduled_time,
        actor="admin",
        actor_id=admin.id,
        reason=reason,
    )

# =========================================================
# ORDERS
# =========================================================

@router.get("/orders")
def list_orders_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_orders(db)

@router.patch("/orders/{order_id}/status")
def update_order_status_api(
    order_id: UUID,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return update_order_status(db, order_id, payload, admin,reason)

@router.patch("/orders/{order_id}/address")
def change_order_address_api(
    order_id: UUID,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return change_order_address(db, order_id, payload, admin,reason)

# =========================================================
# RETURNS & EXCHANGES
# =========================================================

@router.get("/returns")
def list_returns_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_returns(db)

@router.patch("/returns/{return_id}")
def approve_return_api(
    return_id: UUID,
    approved: bool,
    reason: str = Query(...), # Made mandatory to satisfy Audit Log
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # Fix: Call decide_return
    return decide_return(db, return_id, approved, admin.id, reason)

@router.get("/exchanges")
def list_exchanges_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_exchanges(db)

# =========================================================
# COUPONS (GLOBAL ONLY)
# =========================================================

@router.post("/coupons")
def create_coupon_api(
    payload: CouponCreate,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return create_coupon(db, payload, admin,reason)

@router.get("/coupons")
def list_coupons_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_coupons(db)

# =========================================================
# DISCOUNT RULES
# =========================================================

@router.post("/discount-rules")
def create_discount_rule_api(
    payload: ProductDiscountRuleCreate,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return create_product_discount_rule(db, payload, admin,reason)

@router.get("/discount-rules")
def list_discount_rules_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_all_discount_rules(db)

# =========================================================
# OUTBOUND MESSAGING
# =========================================================

@router.get("/outbound/messages")
def list_outbound_messages_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_outbound_messages(db)

# =========================================================
# AI HANDOFFS & AGENT LOGS
# =========================================================

@router.get("/agent/handoffs")
def list_ai_handoffs_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_ai_handoffs(db)

@router.get("/agent/runs")
def list_agent_runs_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_agent_runs(db)

@router.get("/agent/decisions")
def list_decision_records_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_decision_records(db)

# =========================================================
# ML MODEL TRAINING
# =========================================================

@router.post("/ml/train")
def trigger_training_api(
    model_name: str,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return trigger_model_training(db, model_name, admin,reason)

@router.get("/ml/training-runs")
def list_training_runs_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_training_runs(db)

# =========================================================
# ANALYTICS / STATS
# =========================================================

@router.get("/analytics/product-monthly")
def product_monthly_stats_api(
    product_variant_id: UUID | None = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return get_product_monthly_stats(db, product_variant_id)

@router.get("/analytics/product-prices")
def product_price_snapshots_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_product_price_snapshots(db)

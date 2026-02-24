# app/api/routers/admin_global.py


from app.services.post_purchase_agent_service import request_feedback_from_user
from app.services.fulfillment_agent_service import handle_delivery_failure
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.services.support_service import *
from app.core.deps import get_db, get_current_admin
from app.schemas.schemas import *
from app.services.admin_global_service import *
from pydantic import BaseModel

from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.core.deps import get_current_user
from app.core.config import settings
from app.models.models import User

# Import your AI logic
from app.ai.graph import agent_workflow
from app.ai.context_loader import load_context

router = APIRouter(
    prefix="/admin/global",
    tags=["Admin – Global"]
)

# ---------------------------------------------------------
# 1. SETUP POSTGRES CONNECTION POOL FOR LANGGRAPH MEMORY
# ---------------------------------------------------------
# This ensures the agent remembers the user across Web & Kiosk channels.
pool = AsyncConnectionPool(
    conninfo=settings.DATABASE_URL,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0},
)

# ---------------------------------------------------------
# 2. SCHEMAS
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str
    channel: str = "web"

class ChatResponse(BaseModel):
    response: str
    current_agent: Optional[str] = "SalesSupervisor"
    human_takeover: bool = False

class AdminReplyRequest(BaseModel):
    session_id: str
    message: str


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

@router.get("/inventory/kpis")
def get_inventory_kpis_endpoint(db: Session = Depends(get_db)):
    # Make sure to import get_inventory_kpis from your service
    return get_inventory_kpis(db)

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
    payload: ProductImagePayload, # ✅ Now expects JSON body
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return add_product_image(db, variant_id, payload.image_url, admin, reason)

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
async def update_order_status_api(
    order_id: UUID,
    payload: OrderStatusUpdate,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # 👇 FIXED: Added 'await'
    return await update_order_status(db, order_id, payload, admin.id, reason)

@router.patch("/orders/{order_id}/address")
def change_order_address_api(
    order_id: UUID,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    reason: str = Query(...),
    admin=Depends(get_current_admin),
):
    return change_order_address(db, order_id, payload, admin.id,reason)

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
    return create_coupon(db, payload, admin.id ,reason)

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
    return create_product_discount_rule(db, payload, admin.id ,reason)

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



# def list_agent_runs_api(
#     db: Session = Depends(get_db),
#     admin=Depends(get_current_admin),
# ):
#     return list_agent_runs(db)


@router.get("/agent/runs")
def list_agent_runs_api(
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    query = db.query(AgentRun)
    if user_id:
        query = query.filter(AgentRun.user_id == user_id)
    return query.order_by(desc(AgentRun.started_at)).all()


@router.post("/admin-reply")
async def admin_chat_resume(
    request: AdminReplyRequest, 
    current_admin: User = Depends(get_current_user)  # Enforce admin check in real app
):
    """
    Used by the human support dashboard to reply to a user who triggered a handoff.
    This injects the admin's message and resets the agent's failure count.
    """
    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            
            state_update = {
                "messages": [AIMessage(content=f"👨‍💻 [Support Admin]: {request.message}")],
                "pending_human_input": False, 
                "failure_count": 0
            }
            
            await app_graph.ainvoke(state_update, config)
            
        return {"status": "Message injected to thread successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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


@router.get("/complaints", response_model=dict)
def get_all_complaints_api(
    status: Optional[ComplaintStatusEnum] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get all complaints (admin only)"""
    complaints = get_all_complaints(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        category=category
    )
    return {"success": True, "data": complaints}


@router.patch("/complaints/{complaint_id}", response_model=dict)
def update_complaint_api(
    complaint_id: UUID,
    request: ComplaintUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Update complaint status (admin only)"""
    try:
        result = update_complaint_status(
            db=db,
            complaint_id=complaint_id,
            payload=request,
            resolver_id=admin.id,
            resolver_type="admin"
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/complaints/{complaint_id}/respond", response_model=dict)
def respond_to_complaint_api(
    complaint_id: UUID,
    message: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Add response to complaint (admin only)"""
    try:
        result = add_complaint_response(
            db=db,
            complaint_id=complaint_id,
            responder_id=admin.id,
            responder_type="admin",
            message=message
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/complaints/stats", response_model=dict)
def get_complaint_stats_api(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get complaint statistics (admin only)"""
    stats = get_complaint_stats(db=db)
    return {"success": True, "data": stats}



@router.get("/exchanges", response_model=dict)
def get_all_exchanges_api(
    status: Optional[ExchangeStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get all exchanges (admin only)"""
    exchanges = get_all_exchanges(
        db=db,
        skip=skip,
        limit=limit,
        status=status
    )
    return {"success": True, "data": exchanges}


@router.patch("/exchanges/{exchange_id}", response_model=dict)
def update_exchange_api(
    exchange_id: UUID,
    status: ExchangeStatusEnum,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Update exchange status (admin only)"""
    try:
        result = update_exchange_status(
            db=db,
            exchange_id=exchange_id,
            status=status,
            admin_id=admin.id,
            reason=reason
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    

@router.get("/returns", response_model=dict)
def get_all_returns_api(
    status: Optional[ReturnStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get all returns (admin only)"""
    returns = get_all_returns(
        db=db,
        skip=skip,
        limit=limit,
        status=status
    )
    return {"success": True, "data": returns}


@router.patch("/returns/{return_id}/status", response_model=dict)
def update_return_status_api(
    return_id: UUID,
    status: ReturnStatusEnum,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Update return status (admin only)"""
    try:
        result = update_return_status(
            db=db,
            return_id=return_id,
            status=status,
            admin_id=admin.id,
            reason=reason
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/coupons/{coupon_id}")
def delete_coupon_api(
    coupon_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    coupon = db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
        
    db.delete(coupon)
    admin_audit_log(db, admin_id=admin.id, action="delete_coupon", entity_type="coupon", entity_id=coupon_id, reason=reason)
    db.commit()
    return {"status": "deleted"}

@router.put("/coupons/{coupon_id}")
def update_coupon_api(
    coupon_id: UUID,
    payload: CouponCreate, # Reusing the create schema for simplicity
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    coupon = db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
        
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(coupon, k, v)
        
    admin_audit_log(db, admin_id=admin.id, action="update_coupon", entity_type="coupon", entity_id=coupon_id, reason=reason)
    db.commit()
    db.refresh(coupon)
    return coupon

@router.put("/discount-rules/{rule_id}")
def update_discount_rule_api(
    rule_id: UUID,
    payload: ProductDiscountRuleCreate,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    rule = db.get(ProductDiscountRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Discount Rule not found")
        
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(rule, k, v)
        
    admin_audit_log(db, admin_id=admin.id, action="update_discount_rule", entity_type="discount_rule", entity_id=rule_id, reason=reason)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/discount-rules/{rule_id}")
def delete_discount_rule_api(
    rule_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    rule = db.get(ProductDiscountRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Discount Rule not found")
        
    db.delete(rule)
    admin_audit_log(db, admin_id=admin.id, action="delete_discount_rule", entity_type="discount_rule", entity_id=rule_id, reason=reason)
    db.commit()
    return {"status": "deleted"}


@router.get("/inventory/store/{store_id}/variant/{variant_id}")
def get_store_inventory_variant(
    store_id: UUID,
    variant_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    item = get_store_inventory_variant_item(db, store_id, variant_id)

    if not item:
        raise HTTPException(status_code=404, detail="Inventory not found")

    return item


@router.get("/inventory/{variant_id}")
def get_inventory_overview(
    variant_id: UUID,
    store_id: UUID | None = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Returns global + store inventory snapshot.

    If store_id provided → include store inventory.
    """

    data = get_inventory_overview_service(db, variant_id, store_id)

    if not data:
        raise HTTPException(status_code=404, detail="Variant not found")

    return data



from app.services.payment_gateway_config_service import (
    get_gateway_config,
    update_gateway_config,
)

@router.get("/payment-gateway")
def get_payment_gateway_config_api(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin),
):
    cfg = get_gateway_config(db)
    return {
        "force_status": cfg.force_status,
        "updated_at": cfg.updated_at,
    }

@router.post("/payment-gateway")
def set_payment_gateway_config_api(
    force_status: Optional[str] = Query(None, description="Set to 'fail' to simulate failed payments, or None to clear"),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin),
):
    cfg = update_gateway_config(db, force_status=force_status)
    return {
        "force_status": cfg.force_status,
        "updated_at": cfg.updated_at,
    }
    
    
@router.patch("/complaints/{complaint_id}")
async def update_complaint_api(complaint_id: UUID, request: ComplaintUpdateRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        result = await update_complaint_status(db=db, complaint_id=complaint_id, payload=request, resolver_id=admin.id, resolver_type="admin")
        return {"success": True, "data": result}
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))

@router.post("/complaints/{complaint_id}/respond")
async def respond_to_complaint_api(complaint_id: UUID, message: str, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        result = await add_complaint_response(db=db, complaint_id=complaint_id, responder_id=admin.id, responder_type="admin", message=message)
        return {"success": True, "data": result}
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))

@router.patch("/exchanges/{exchange_id}")
async def update_exchange_api(exchange_id: UUID, status: ExchangeStatusEnum, reason: Optional[str] = None, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        result = await update_exchange_status(db=db, exchange_id=exchange_id, status=status, admin_id=admin.id, reason=reason)
        return {"success": True, "data": result}
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))

@router.patch("/returns/{return_id}/status")
async def update_return_status_api(return_id: UUID, status: ReturnStatusEnum, reason: Optional[str] = None, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        result = await update_return_status(db=db, return_id=return_id, status=status, admin_id=admin.id, reason=reason)
        return {"success": True, "data": result}
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))
    
    
    
@router.post("/orders/{order_id}/delivery-failed")
async def report_delivery_failure(
    order_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    return await handle_delivery_failure(db, order_id, reason)


@router.post("/orders/{order_id}/request-feedback")
async def request_feedback(
    order_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return await request_feedback_from_user(db, order_id)
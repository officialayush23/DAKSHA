# app/services/admin_global_service.py

from itertools import product
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from shapely.geometry import shape
from geoalchemy2.shape import from_shape
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from app.models.models import (
    Product,
    ProductVariant,
    ProductImage,
    ProductMultimodalEmbedding,
    GlobalInventory,
    StoreInventory,
    Store,
    Kiosk,
    Pickup,
    Return,
    Exchange,
    Order,
    OrderStatusHistory,
    Coupon,
    CouponEmbedding,
    OutboundMessage,
    AgentHandoff,
    AgentRun,
    DecisionRecord,
    ModelTrainingRun,
    ProductDiscountRule,
    ProductPriceSnapshot,
    ProductMonthlyStats,
)
from app.enums.db_enums import *
from app.services.embedding_service import generate_text_embedding
from app.services.product_embedding_service import (
    upsert_variant_text_embedding,
    upsert_variant_image_embeddings, # Wrapper wrapper
)
from app.services.coupon_embedding_service import upsert_coupon_embedding


# =========================================================
# ADMIN AUDIT + AGENT LOGGING (MANDATORY)
# =========================================================


def admin_audit_log(
    db: Session,
    *,
    admin_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[uuid.UUID],
    reason: str,
    source: str = "admin",
):
    db.add(
        DecisionRecord(
            user_id=admin_id,
            decision_type=action,
            decision_output={
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "source": source,
            },
            rationale=reason,
        )
    )

def log_agent_action(
    db: Session,
    *,
    agent_name: str,
    agent_role: str,
    session_id: Optional[uuid.UUID],
    user_id: Optional[uuid.UUID],
    trigger_event: str,
    confidence: Optional[float],
    metadata: Optional[Dict[str, Any]] = None,
):
    run = AgentRun(
        session_id=session_id,
        user_id=user_id,
        agent_name=agent_name,
        agent_role=agent_role,
        trigger_event=trigger_event,
        status="completed",
        confidence=confidence,
        run_metadata=metadata,
    )
    db.add(run)
    return run


# =========================================================
# PRODUCTS
# =========================================================

# =========================================================
# 1. CATALOG MANAGEMENT
# =========================================================

def create_product(db: Session, payload, admin_id, reason: str):
    product = Product(**payload.dict(exclude={"variants"})) # Handle variants separately if nested
    db.add(product)
    db.flush() # Get ID

    # Handle nested variants if present in Pydantic schema
    if hasattr(payload, 'variants') and payload.variants:
        for v_data in payload.variants:
            create_variant(
    db,
    payload=v_data,
    admin_id=admin_id,
    reason="Initial creation",
    product_id=product.id,
)


    admin_audit_log(db, admin_id=admin_id, action="create_product", entity_type="product", entity_id=product.id, reason=reason)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id, payload, admin_id, reason: str):
    product = db.get(Product, product_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(product, k, v)

    db.commit()
    db.refresh(product)

    # 🔥 RE-EMBED ALL VARIANTS
    for v in product.variants:
        upsert_variant_text_embedding(db, v.id)

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="update_product",
        entity_type="product",
        entity_id=product_id,
        reason=reason,
    )
    return product


def delete_product(db: Session, product_id, admin_id, reason: str):

    variants = db.query(ProductVariant.id).filter(
        ProductVariant.product_id == product_id
    ).all()

    for v in variants:
        delete_variant(db, v.id, admin_id, "cascade delete")

    db.query(Product).filter(Product.id == product_id).delete()

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="delete_product",
        entity_type="product",
        entity_id=product_id,
        reason=reason,
    )

    db.commit()


# =========================================================
# VARIANTS (+ EMBEDDINGS AUTO)
# =========================================================

from app.services.product_embedding_service import (
    upsert_variant_text_embedding,
    upsert_variant_image_embeddings,
)

def create_variant(db: Session, payload, admin_id, reason: str, product_id: uuid.UUID = None):
    data = payload.dict()
    if product_id:
        data['product_id'] = product_id
    
    variant = ProductVariant(**data)
    db.add(variant)
    db.commit()
    db.refresh(variant)

    # 🔥 AUTO-EMBEDDING GENERATION
    upsert_variant_text_embedding(db, variant.id)
    
    admin_audit_log(db, admin_id=admin_id, action="create_variant", entity_type="product_variant", entity_id=variant.id, reason=reason)
    return variant

def add_product_image(db, variant_id: uuid.UUID, image_url: str, admin_id: uuid.UUID, reason: str):
    pos = db.query(func.max(ProductImage.position)).filter(
        ProductImage.product_variant_id == variant_id
    ).scalar() or 0

    img = ProductImage(
        product_variant_id=variant_id,
        image_url=image_url,
        position=pos + 1
    )

    db.add(img)
    db.commit()

    # 🔥 Sync embeddings
    upsert_variant_image_embeddings(db, variant_id)
    upsert_variant_text_embedding(db, variant_id)

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="add_product_image",
        entity_type="product_image",
        entity_id=variant_id,
        reason=reason,
    )

    return img

def get_inventory_kpis(db: Session):
    total_variants = db.query(func.count(ProductVariant.id)).scalar() or 0
    
    # Total stock across the entire system
    global_stock = db.query(func.sum(GlobalInventory.total_stock)).scalar() or 0
    
    # Stock that is physically currently at stores
    store_stock = db.query(func.sum(StoreInventory.in_stock)).scalar() or 0
    
    # Stock sitting in the global warehouse (reserved/unassigned to stores yet)
    warehouse_stock = db.query(func.sum(GlobalInventory.reserved_stock)).scalar() or 0
    
    return {
        "total_variants_tracked": total_variants,
        "total_global_stock": global_stock,
        "stock_at_stores": store_stock,
        "stock_in_warehouse": warehouse_stock
    }
    
def update_variant(db: Session, variant_id, payload, admin_id, reason: str):
    variant = db.get(ProductVariant, variant_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(variant, k, v)

    db.commit()
    on_pricing_change(db, variant.id)
    upsert_variant_text_embedding(db, variant.id)

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="update_variant",
        entity_type="product_variant",
        entity_id=variant_id,
        reason=reason,
    )
    return variant

def on_pricing_change(db: Session, variant_id):
    variant = db.get(ProductVariant, variant_id)
    if not variant:
        return
    apply_active_discount_rules(db, variant)

def delete_variant(db: Session, variant_id, admin_id, reason: str):

    db.query(ProductMultimodalEmbedding).filter(
        ProductMultimodalEmbedding.product_variant_id == variant_id
    ).delete()

    db.query(ProductImage).filter(
        ProductImage.product_variant_id == variant_id
    ).delete()

    db.query(ProductVariant).filter(
        ProductVariant.id == variant_id
    ).delete()

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="delete_variant",
        entity_type="product_variant",
        entity_id=variant_id,
        reason=reason,
    )

    db.commit()


# =========================================================
# INVENTORY (GLOBAL + STORE ALLOCATION)
# =========================================================
def assert_global_inventory_consistency(inv: GlobalInventory):
    if inv.assigned_stock < 0 or inv.reserved_stock < 0:
        raise ValueError("Inventory cannot go negative")
    if inv.assigned_stock + inv.reserved_stock != inv.total_stock:
        raise ValueError("GlobalInventory invariant violated")

# =========================================================
# 2. INVENTORY & STORES
# =========================================================

def assign_global_inventory(db: Session, payload, admin_id, reason: str):
    inv = db.get(GlobalInventory, payload.product_variant_id)
    if not inv:
        inv = GlobalInventory(
    product_variant_id=payload.product_variant_id,
    total_stock=payload.quantity,
    reserved_stock=payload.quantity,
    assigned_stock=0
)
        db.add(inv)
    else:
        inv.total_stock += payload.quantity
        inv.reserved_stock += payload.quantity
    
    admin_audit_log(db, admin_id=admin_id, action="assign_global_inventory", entity_type="global_inventory", entity_id=payload.product_variant_id, reason=reason)
    assert_global_inventory_consistency(inv)
    db.commit()
    return inv



def assign_store_inventory(db: Session, payload, admin_id, reason: str):
    global_inv = db.get(GlobalInventory, payload.product_variant_id)
    if not global_inv or global_inv.reserved_stock < payload.quantity:
        raise ValueError("Insufficient global stock")

    store_inv = db.query(StoreInventory).filter_by(
        store_id=payload.store_id,
        product_variant_id=payload.product_variant_id,
    ).first()

    if not store_inv:
        store_inv = StoreInventory(
            store_id=payload.store_id,
            product_variant_id=payload.product_variant_id,
            in_stock=payload.quantity,
            reserved_for_pickup=0,
        )
        db.add(store_inv)
    else:
        store_inv.in_stock += payload.quantity

    global_inv.reserved_stock -= payload.quantity
    global_inv.assigned_stock += payload.quantity

    assert_global_inventory_consistency(global_inv)

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="assign_store_inventory",
        entity_type="store_inventory",
        entity_id=payload.product_variant_id,
        reason=reason,
    )
    db.commit()
    return store_inv


# =========================================================
# STORES + KIOSKS
# =========================================================


def serialize_store(store):
    geojson = None
    if store.location:
        geojson = mapping(to_shape(store.location))

    return {
        "id": store.id,
        "name": store.name,
        "city": store.city,
        "state": store.state,
        "address": store.address,
        "active": store.active,
        "location": geojson,
    }
    
def create_store(db: Session, payload, admin_id, reason: str):
    # Fix: Ensure we pass a Dict to shape(), not a Pydantic model
    loc_data = payload.location.dict() if hasattr(payload.location, 'dict') else payload.location
    loc_shape = shape(loc_data) 
    
    store = Store(
        name=payload.name, city=payload.city, state=payload.state, address=payload.address,
        location=from_shape(loc_shape, srid=4326)
    )
    db.add(store)
    db.commit()
    admin_audit_log(db, admin_id=admin_id, action="create_store", entity_type="store", entity_id=store.id, reason=reason)
    return serialize_store(store) 



def create_kiosk(db: Session, payload, admin_id, reason: str):
    kiosk = Kiosk(**payload.dict())
    db.add(kiosk)
    db.commit()

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="create_kiosk",
        entity_type="kiosk",
        entity_id=kiosk.id,
        reason=reason,
    )
    return kiosk


# =========================================================
# PICKUPS (ADMIN + AI RESCHEDULE)
# =========================================================

def update_pickup(
    db: Session,
    pickup_id: uuid.UUID,
    *,
    status: Optional[str] = None,
    scheduled_time: Optional[datetime] = None,
    actor: str,
    actor_id: Optional[uuid.UUID],
    reason: str,
):
    pickup = db.get(Pickup, pickup_id)
    if not pickup:
        raise ValueError("Pickup not found")

    if status:
        pickup.status = status
    if scheduled_time:
        pickup.scheduled_time = scheduled_time

    admin_audit_log(
        db,
        admin_id=actor_id if actor == "admin" else None,
        action="update_pickup",
        entity_type="pickup",
        entity_id=pickup_id,
        reason=reason,
        source=actor,
    )

    db.commit()
    return pickup

# =========================================================
# RETURNS & EXCHANGES
# =========================================================

def decide_return(
    db: Session,
    return_id,
    approved: bool,
    decided_by,
    reason: str,
):
    r = db.get(Return, return_id)
    r.status = ReturnStatusEnum.approved if approved else ReturnStatusEnum.rejected

    admin_audit_log(
        db,
        admin_id=decided_by,
        action="decide_return",
        entity_type="return",
        entity_id=return_id,
        reason=reason,
    )
    db.commit()
    return r


def decide_exchange(
    db: Session,
    exchange_id,
    approved: bool,
    decided_by,
    reason: str,
):
    e = db.get(Exchange, exchange_id)
    e.status = ExchangeStatusEnum.approved if approved else ExchangeStatusEnum.rejected

    admin_audit_log(
        db,
        admin_id=decided_by,
        action="decide_exchange",
        entity_type="exchange",
        entity_id=exchange_id,
        reason=reason,
    )
    db.commit()
    return e


# =========================================================
# ORDER MUTATIONS (STATUS / ADDRESS / ITEMS)
# =========================================================
def update_order_status(db: Session, order_id: uuid.UUID, payload, admin_id, reason: str):
    order = db.get(Order, order_id)
    if not order: raise ValueError("Order not found")
    
    order.order_status = payload.status
    db.add(OrderStatusHistory(order_id=order_id, status=payload.status, description=payload.description))
    
    # Trigger Sales Facts if confirmed
    if payload.status == OrderStatusEnum.confirmed:
        # (This logic is usually in a DB trigger, but can be explicit here too)
        pass

    admin_audit_log(db, admin_id=admin_id, action="update_order_status", entity_type="order", entity_id=order_id, reason=reason)
    db.commit()
    return order



# =========================================================
# OUTBOUND MESSAGING + LOGS
# =========================================================

def send_outbound_message(
    db: Session,
    payload,
    admin_id,
    reason: str,
):
    msg = OutboundMessage(**payload.dict())
    db.add(msg)

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="send_outbound_message",
        entity_type="outbound_message",
        entity_id=msg.id,
        reason=reason,
    )
    db.commit()
    return msg



# =========================================================
# ML MODEL TRAINING
# =========================================================

def trigger_model_training(
    db: Session,
    model_name: str,
    admin_id,
    reason: str,
):
    run = ModelTrainingRun(
        model_name=model_name,
        trigger_source="admin",
        status=TrainingRunStatusEnum.started,
    )
    db.add(run)

    admin_audit_log(
        db,
        admin_id=admin_id,
        action="trigger_model_training",
        entity_type="model_training",
        entity_id=run.id,
        reason=reason,
    )
    db.commit()
    return run

def apply_active_discount_rules(db: Session, variant: ProductVariant):
    
    now = datetime.utcnow()


    rules = (
        db.query(ProductDiscountRule)
        .filter(
            ProductDiscountRule.active.is_(True),
            ProductDiscountRule.valid_from <= now,
            (ProductDiscountRule.valid_to.is_(None) | (ProductDiscountRule.valid_to >= now))
        )
        .all()
    )

    applicable = []
    for r in rules:
        if r.product_ids_filter and variant.id not in r.product_ids_filter:
            continue
        if r.category_filter and variant.product.category != r.category_filter:
            continue
        if r.brand_filter and variant.product.brand != r.brand_filter:
            continue
        applicable.append(r)

    if not applicable:
        return None

    best = max(applicable, key=lambda r: float(r.value))

    if best.discount_type == CouponTypeEnum.percentage:
        discount_percent = best.value
        display_price = variant.base_price * (1 - float(best.value) / 100)

    else:
        discount_percent = None
        display_price = max(variant.base_price - float(best.value), 0)


    snapshot = ProductPriceSnapshot(
        product_variant_id=variant.id,
        base_price=variant.base_price,
        display_price=display_price,
        discount_percent=discount_percent,
        discount_reason=best.name,
    )

    db.merge(snapshot)
    db.commit()
    return snapshot

def list_all_discount_rules(db: Session): 
    return db.query(ProductDiscountRule).order_by(ProductDiscountRule.created_at.desc()).all()

def list_all_stores(db: Session):
    stores = db.query(Store).all()
    return [serialize_store(s) for s in stores]

def list_all_orders(db: Session):
    return db.query(Order).order_by(Order.created_at.desc()).all()

def list_all_returns(db: Session):
    return db.query(Return).order_by(Return.created_at.desc()).all()

def list_all_exchanges(db: Session):
    return db.query(Exchange).order_by(Exchange.created_at.desc()).all()

def list_all_pickups(db: Session):
    return db.query(Pickup).order_by(Pickup.updated_at.desc()).all()

def list_all_coupons(db: Session):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()

def list_all_kiosks(db: Session):
    return db.query(Kiosk).order_by(Kiosk.created_at.desc()).all()

# =======================
# LISTING HELPERS
# =======================

def list_all_products(db: Session):
    return (
        db.query(Product)
        .options(joinedload(Product.variants))
        .order_by(Product.created_at.desc())
        .all()
    )

def get_product(db: Session, product_id):
    return db.get(Product, product_id)

def list_all_variants(db: Session):
    return (
        db.query(ProductVariant)
        .options(joinedload(ProductVariant.images))
        .order_by(ProductVariant.created_at.desc())
        .all()
    )

def get_variant(db: Session, variant_id):
    return db.get(ProductVariant, variant_id)

def list_global_inventory(db: Session):
    return db.query(GlobalInventory).all()

def list_store_inventory(db: Session):
    return db.query(StoreInventory).all()

def list_outbound_messages(db: Session):
    return db.query(OutboundMessage).order_by(OutboundMessage.created_at.desc()).all()

def list_ai_handoffs(db: Session):
    return db.query(AgentHandoff).order_by(AgentHandoff.created_at.desc()).all()

def list_agent_runs(db: Session):
    return db.query(AgentRun).order_by(AgentRun.started_at.desc()).all()

def list_decision_records(db: Session):
    return db.query(DecisionRecord).order_by(DecisionRecord.created_at.desc()).all()

def list_training_runs(db: Session):
    return db.query(ModelTrainingRun).order_by(ModelTrainingRun.started_at.desc()).all()

def get_product_monthly_stats(db: Session, product_variant_id=None):
    q = db.query(ProductMonthlyStats)
    if product_variant_id:
        q = q.filter(ProductMonthlyStats.product_variant_id == product_variant_id)
    return q.order_by(
        ProductMonthlyStats.year.desc(),
        ProductMonthlyStats.month.desc()
    ).all()

def list_product_price_snapshots(db: Session):
    return db.query(ProductPriceSnapshot)\
        .order_by(ProductPriceSnapshot.computed_at.desc())\
        .all()



# =========================================================
# 3. ORDER OPS & LOGISTICS
# =========================================================


def change_order_address(db: Session, order_id: uuid.UUID, payload, admin_id, reason: str):
    order = db.get(Order, order_id)
    if order.mutability_state == OrderMutabilityEnum.shipped:
        raise ValueError("Cannot change address of shipped order")
    
    # Construct address string
    new_addr = f"{payload.address_line}, {payload.city}, {payload.state} - {payload.pincode}"
    old_addr = order.delivery_address
    order.delivery_address = new_addr
    
    admin_audit_log(db, admin_id=admin_id, action="change_order_address", entity_type="order", entity_id=order_id, reason=f"{reason} | Old: {old_addr}")
    db.commit()
    return order



# =========================================================
# 4. MARKETING & AI
# =========================================================

def create_coupon(db: Session, payload, admin_id, reason: str):
    coupon = Coupon(**payload.dict())
    db.add(coupon)
    db.flush()
    upsert_coupon_embedding(db, coupon.id) # Vectorize for Agents
    admin_audit_log(db, admin_id=admin_id, action="create_coupon", entity_type="coupon", entity_id=coupon.id, reason=reason)
    db.commit()
    return coupon
from app.models.models import StoreInventory

def get_store_inventory_variant_item(db, store_id, variant_id):
    return (
        db.query(StoreInventory)
        .filter(
            StoreInventory.store_id == store_id,
            StoreInventory.product_variant_id == variant_id,
        )
        .first()
    )
    
    
from app.models.models import GlobalInventory, StoreInventory, ProductVariant


def get_inventory_overview_service(db, variant_id, store_id=None):
    variant = db.get(ProductVariant, variant_id)
    if not variant:
        return None

    # --- GLOBAL ---
    global_inv = db.get(GlobalInventory, variant_id)

    global_data = {
        "total_stock": global_inv.total_stock if global_inv else 0,
        "reserved_stock": global_inv.reserved_stock if global_inv else 0,
        "assigned_stock": global_inv.assigned_stock if global_inv else 0,
    }

    global_available = (
        global_data["total_stock"]
        - global_data["reserved_stock"]
        - global_data["assigned_stock"]
    )

    # --- STORE ---
    store_data = None

    if store_id:
        store_inv = (
            db.query(StoreInventory)
            .filter(
                StoreInventory.store_id == store_id,
                StoreInventory.product_variant_id == variant_id,
            )
            .first()
        )

        store_data = {
            "in_stock": store_inv.in_stock if store_inv else 0,
            "reserved_for_pickup": store_inv.reserved_for_pickup if store_inv else 0,
        }

        store_data["available"] = (
            store_data["in_stock"] - store_data["reserved_for_pickup"]
        )

    return {
        "variant_id": variant_id,
        "global": {
            **global_data,
            "available": global_available,
        },
        "store": store_data,
    }
    
def create_product_discount_rule(db: Session, payload, admin_id: uuid.UUID, reason: str):
    rule = ProductDiscountRule(**payload.dict())
    db.add(rule)
    db.flush() # Ensure the rule gets an ID before logging
    admin_audit_log(db, admin_id=admin_id, action="create_discount_rule", entity_type="discount_rule", entity_id=rule.id, reason=reason)
    db.commit()
    db.refresh(rule) # Refresh to return the full object
    return rule


def list_active_handoffs(db: Session):
    return db.query(AgentHandoff).filter(AgentHandoff.status == ComplaintStatusEnum.open).order_by(AgentHandoff.created_at.desc()).all()


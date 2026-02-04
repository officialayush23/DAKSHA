# app/services/admin_services.py
from sqlalchemy.orm import Session,joinedload
from sqlalchemy import func,desc
from shapely.geometry import shape
from geoalchemy2.shape import from_shape
import uuid
from app.services.product_embedding_service import (
    upsert_product_variant_embedding
)
from app.models.models import *
from app.enums.db_enums import *
from app.services.embedding_service import generate_embedding
from app.models.models import UserSession, ConversationSummary
# ================= 1. PRODUCTS & VARIANTS =================

def create_product(db: Session, payload):
    product = Product(**payload.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def update_product(db: Session, product_id, payload):
    product = db.query(Product).filter_by(id=product_id).first()

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(product, k, v)

    db.commit()

    # 🔥 RE-EMBED ALL VARIANTS
    for variant in product.variants:
        upsert_product_variant_embedding(db, variant.id)

    return product


def delete_product(db: Session, product_id):
    db.query(Product).filter(Product.id == product_id).delete()
    db.commit()

def create_variant(db: Session, payload):
    variant = ProductVariant(
        product_id=payload.product_id,
        sku=payload.sku,
        color=payload.color,
        size=payload.size,
        base_price=payload.base_price,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)

    try:
        upsert_product_variant_embedding(db, variant.id)
    except Exception as e:
        # log but DO NOT fail admin operation
        print(f"[EMBEDDING FAILED] variant={variant.id} err={e}")

    return variant


def update_variant(db: Session, variant_id, payload):
    variant = db.query(ProductVariant).filter_by(id=variant_id).first()

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(variant, k, v)

    db.commit()

    # 🔥 RE-EMBED
    upsert_product_variant_embedding(db, variant.id)

    return variant

from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

def serialize_store(store: Store):
    return {
        "id": store.id,
        "name": store.name,
        "city": store.city,
        "state": store.state,
        "address": store.address,
        "location": mapping(to_shape(store.location)),
    }

def delete_variant(db: Session, variant_id):
    db.query(ProductVariant).filter(ProductVariant.id == variant_id).delete()
    db.commit()

def add_variant_image(db: Session, variant_id, payload):
    image = ProductImage(
        product_variant_id=variant_id,
        image_url=payload.image_url,
        position=payload.position
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image

# ================= 2. STORES & KPIS =================

def create_store(db: Session, payload):
    # Convert GeoJSON dict to PostGIS Geometry
    point = shape(payload.location) 
    store = Store(
        name=payload.name,
        city=payload.city,
        state=payload.state,
        address=payload.address,
        location=from_shape(point, srid=4326),
        active=True
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store

def update_store(db: Session, store_id, payload):
    store = db.query(Store).get(store_id)
    if not store: return None
    data = payload.dict(exclude_unset=True)
    
    if "location" in data:
        store.location = from_shape(shape(data.pop("location")), srid=4326)
    
    for k, v in data.items():
        setattr(store, k, v)
    
    db.commit()
    return store

def store_kpis(db: Session, store_id):
    return {
        "store_id": store_id,
        "total_pickups": db.query(Pickup).filter(Pickup.store_id == store_id).count(),
        "pending_pickups": db.query(Pickup).filter(Pickup.store_id == store_id, Pickup.status == PickupStatusEnum.pending).count(),
        "completed_pickups": db.query(Pickup).filter(Pickup.store_id == store_id, Pickup.status == PickupStatusEnum.picked_up).count()
    }

# ================= 3. INVENTORY (GLOBAL & STORE) =================

def assign_global_inventory(db: Session, payload):
    inv = db.query(GlobalInventory).get(payload.product_variant_id)
    if not inv:
        inv = GlobalInventory(
            product_variant_id=payload.product_variant_id,
            total_stock=payload.quantity,
            reserved_stock=payload.quantity, # Initially unassigned
            assigned_stock=0
        )
        db.add(inv)
    else:
        inv.total_stock += payload.quantity
        inv.reserved_stock += payload.quantity
    db.commit()
    return inv

def assign_store_inventory(db: Session, payload):
    # Logic: Move stock from Global Reserved -> Store In Stock
    global_inv = db.query(GlobalInventory).get(payload.product_variant_id)
    
    # Check strict constraints
    if not global_inv or global_inv.reserved_stock < payload.quantity:
        raise ValueError("Insufficient Global Reserved Stock")
        
    store_inv = db.query(StoreInventory).filter(
        StoreInventory.store_id == payload.store_id,
        StoreInventory.product_variant_id == payload.product_variant_id
    ).first()

    if not store_inv:
        store_inv = StoreInventory(
            store_id=payload.store_id,
            product_variant_id=payload.product_variant_id,
            in_stock=payload.quantity,
            reserved_for_pickup=0
        )
        db.add(store_inv)
    else:
        store_inv.in_stock += payload.quantity

    # Deduct from Global Reserved and Move to Assigned
    global_inv.reserved_stock -= payload.quantity
    global_inv.assigned_stock += payload.quantity
    
    db.commit()
    return store_inv

def get_global_inventory(db: Session, product_id):
    # Join with Variants to get all variants for a product
    return db.query(GlobalInventory).join(ProductVariant)\
             .filter(ProductVariant.product_id == product_id).all()

def get_store_inventory(db: Session, store_id, product_id):
    return db.query(StoreInventory).join(ProductVariant)\
             .filter(StoreInventory.store_id == store_id, ProductVariant.product_id == product_id).all()
             
def global_inventory_kpis(db: Session):
    return {
        "total_variants_tracked": db.query(GlobalInventory).count(),
        "total_global_stock": db.query(func.sum(GlobalInventory.total_stock)).scalar() or 0,
        "stock_at_stores": db.query(func.sum(GlobalInventory.assigned_stock)).scalar() or 0,
        "stock_in_warehouse": db.query(func.sum(GlobalInventory.reserved_stock)).scalar() or 0
    }

# ================= 4. PICKUPS =================

def update_pickup_status(db: Session, pickup_id, payload):
    pickup = db.query(Pickup).get(pickup_id)
    if not pickup: return None
    pickup.status = payload.status
    db.commit()
    return pickup

# ================= 5. HANDOFF DASHBOARD =================



def active_handoffs(db: Session):
    rows = (
        db.query(UserSession, ConversationSummary)
        .outerjoin(
            ConversationSummary,
            UserSession.id == ConversationSummary.session_id
        )
        .filter(UserSession.ended_at.is_(None))
        .all()
    )

    return [
        {
            "session_id": session.id,
            "user_id": session.user_id,
            "channel": session.active_channel,
            "started_at": session.started_at,
            "summary": summary.summary_text if summary else "No summary yet",
        }
        for session, summary in rows
    ]


# ================= 6. COMPLAINTS =================

def create_complaint(db: Session, payload):
    complaint = Complaint(**payload.dict())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint

def list_complaints(db: Session, status: str = None):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    return query.all()

def update_complaint(db: Session, complaint_id, payload):
    c = db.query(Complaint).get(complaint_id)
    if not c: return None
    c.status = payload.status
    c.resolution_notes = payload.resolution_notes
    db.commit()
    return c

# --- HELPER: Offer Embedding ---
def upsert_offer_embedding(db: Session, offer_id):
    offer = db.query(Offer).get(offer_id)
    if not offer: return
    # Create semantic text for the offer
    text = f"Offer: {offer.name}. Category: {offer.eligible_category}. Discount: {offer.discount_value} {offer.discount_type}."
    vector = generate_embedding(text)
    
    emb = db.query(OfferEmbedding).get(offer_id)
    if emb:
        emb.embedding = vector
    else:
        db.add(OfferEmbedding(offer_id=offer_id, embedding=vector))
    db.commit()

# ================= 1. PRODUCTS & VARIANTS =================
def get_all_products(db: Session, limit: int = 100, offset: int = 0):
    return db.query(Product).order_by(desc(Product.created_at)).limit(limit).offset(offset).all()

def get_product_variants(db: Session, product_id):
    # Eager load images to avoid N+1 queries
    return db.query(ProductVariant).options(joinedload(ProductVariant.images))\
             .filter(ProductVariant.product_id == product_id).all()

def get_all_images(db: Session, limit: int = 100):
    return db.query(ProductImage).limit(limit).all()

# ================= 2. STORES =================
def get_all_stores(db: Session):
    rows = (
        db.query(
            Store.id,
            Store.name,
            Store.city,
            Store.state,
            Store.address,
            func.ST_AsGeoJSON(Store.location).label("location"),
            Store.active,
        )
        .filter(Store.active == True)
        .all()
    )

    return [
        {
            "id": r.id,
            "name": r.name,
            "city": r.city,
            "state": r.state,
            "address": r.address,
            "location": r.location,  # already JSON string
            "active": r.active,
        }
        for r in rows
    ]

def get_store_pickups(db: Session, store_id):
    return db.query(Pickup).filter(Pickup.store_id == store_id).order_by(desc(Pickup.updated_at)).all()


# ================= 7. OFFERS =================
def create_offer(db: Session, payload):
    offer = Offer(**payload.dict())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    # 🔥 Generate Embedding
    upsert_offer_embedding(db, offer.id)
    return offer

def update_offer(db: Session, offer_id, payload):
    offer = db.query(Offer).get(offer_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(offer, k, v)
    db.commit()
    # 🔥 Re-Embed
    upsert_offer_embedding(db, offer.id)
    return offer

def get_all_offers(db: Session):
    return db.query(Offer).order_by(desc(Offer.valid_to)).all()


def delete_offer(db: Session, offer_id):
    db.query(Offer).filter(Offer.id == offer_id).delete()
    db.commit()

# ================= 8. DELIVERY =================

def update_order_status(db: Session, order_id, payload):
    order = db.query(Order).get(order_id)
    if not order: return None
    
    order.order_status = payload.status
    
    # Log History
    history = OrderStatusHistory(
        id=uuid.uuid4(),
        order_id=order_id,
        status=payload.status,
        description=payload.description
    )
    db.add(history)
    db.commit()
    return order

def get_delivery_details(db: Session, order_id):
    return db.query(Order).filter(Order.id == order_id).first()


# ================= PUBLIC OFFER ACCESS =================

def list_offers(db: Session):
    """
    Public-safe offer listing for agents / users.
    Filters inactive & expired offers.
    """
    now = func.now()
    return (
        db.query(Offer)
        .filter(
            Offer.active.is_(True),
            Offer.valid_from <= now,
            Offer.valid_to >= now,
        )
        .order_by(desc(Offer.valid_to))
        .all()
    )

def create_kiosk(db: Session, payload):
    kiosk = Kiosk(
        store_id=payload.store_id,
        name=payload.name,
        active=True,
    )
    db.add(kiosk)
    db.commit()
    db.refresh(kiosk)
    return kiosk

def list_kiosks(db: Session):
    return db.query(Kiosk).options(joinedload(Kiosk.store)).all()

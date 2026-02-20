# app/models/models.py
import uuid
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    String, Boolean, ForeignKey, Numeric, Integer, Text, DateTime,
    ARRAY, UniqueConstraint, Index, func, PrimaryKeyConstraint
)

from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from geoalchemy2 import Geography
from app.enums import db_enums

class Base(DeclarativeBase):
    pass

# ==========================================
# 1. USER & IDENTITY
# ==========================================

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[Optional[str]]
    email: Mapped[Optional[str]] = mapped_column(unique=True)
    phone: Mapped[Optional[str]] = mapped_column(unique=True)
    gender: Mapped[Optional[str]]
    loyalty_tier: Mapped[Optional[str]]
    role: Mapped[db_enums.UserRoleEnum] = mapped_column(default=db_enums.UserRoleEnum.user)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
   

    loyalty_history: Mapped[List["LoyaltyLedger"]] = relationship(back_populates="user")
    personalized_offers: Mapped[List["UserPersonalizedOffer"]] = relationship(back_populates="user")
    agent_handoffs: Mapped[List["AgentHandoff"]] = relationship(
    "AgentHandoff",
    foreign_keys="AgentHandoff.user_id",
    back_populates="user",
)
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    carts: Mapped[List["Cart"]] = relationship(back_populates="user")
    cards: Mapped[List["UserCard"]] = relationship(back_populates="user")
    preferences: Mapped[Optional["UserPreferences"]] = relationship(back_populates="user")
    wishlist: Mapped[List["UserWishlist"]] = relationship(back_populates="user")
    behavior: Mapped[Optional["UserBehaviorAggregate"]] = relationship(back_populates="user")
    addresses: Mapped[List["UserAddress"]] = relationship(back_populates="user")
    telegram_info: Mapped[Optional["TelegramUser"]] = relationship(back_populates="user")
class TelegramUser(Base):
    __tablename__ = "telegram_users"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[str] = mapped_column(unique=True)
    username: Mapped[Optional[str]]
    opt_in: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="telegram_info")
class UserCard(Base):
    __tablename__ = "user_cards"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    card_brand: Mapped[db_enums.CardBrandEnum]
    card_last4: Mapped[str] = mapped_column(String(4))
    token: Mapped[str] = mapped_column(unique=True)
    card_name: Mapped[Optional[str]]
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="cards")
    __table_args__ = (Index("one_default_card_per_user", "user_id", unique=True, postgresql_where=(is_default == True)),)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    preferred_categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    excluded_categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    preferred_price_min: Mapped[Optional[float]] = mapped_column(Numeric)
    preferred_price_max: Mapped[Optional[float]] = mapped_column(Numeric)
    preferred_fulfillment: Mapped[Optional[db_enums.FulfillmentTypeEnum]]
    min_acceptable_rating: Mapped[Optional[float]] = mapped_column(Numeric)
    preferred_sizes: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    preferred_colors: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    updated_by: Mapped[Optional[str]]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship(back_populates="preferences")

class UserBehaviorAggregate(Base):
    __tablename__ = "user_behavior_aggregates"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    most_viewed_categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    avg_viewed_price: Mapped[Optional[float]] = mapped_column(Numeric)
    most_common_size: Mapped[Optional[str]]
    most_common_color: Mapped[Optional[str]]
    last_computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="behavior")
class UserWishlist(Base):
    __tablename__ = "user_wishlist"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="wishlist")
    variant: Mapped["ProductVariant"] = relationship()

class UserLocation(Base):
    __tablename__ = "user_locations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"), unique=True)
    location: Mapped[str] = mapped_column(Geography('POINT', srid=4326))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

# ==========================================
# 2. SESSION & CONVERSATION
# ==========================================

class UserSession(Base):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    primary_channel: Mapped[Optional[db_enums.ChannelEnum]]
    active_channel: Mapped[Optional[db_enums.ChannelEnum]]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    anonymous_id: Mapped[Optional[uuid.UUID]]
    user: Mapped["User"] = relationship(back_populates="sessions")
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="session")
    summary: Mapped[Optional["ConversationSummary"]] = relationship(back_populates="session")
    checkouts: Mapped[List["CheckoutSession"]] = relationship(back_populates="session")
    events: Mapped[List["Event"]] = relationship(back_populates="session")
    context: Mapped[Dict[str, Any]] = mapped_column(
    JSONB,
    default=dict
)

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    channel: Mapped[Optional[db_enums.ChannelEnum]]
    speaker: Mapped[Optional[str]]
    message: Mapped[Optional[str]] = mapped_column(Text)
    intent: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    session: Mapped["UserSession"] = relationship(back_populates="conversations")

class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"), primary_key=True)
    summary_text: Mapped[Optional[str]] = mapped_column(Text)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    session: Mapped["UserSession"] = relationship(back_populates="summary")

class UserIntent(Base):
    __tablename__ = "user_intents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))
    intent_text: Mapped[Optional[str]] = mapped_column(Text)
    intent_category: Mapped[Optional[str]]
    confidence: Mapped[Optional[float]] = mapped_column(Numeric)
    intent_tsv: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# ==========================================
# 3. CATALOG
# ==========================================

class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    brand: Mapped[Optional[str]]
    category: Mapped[Optional[str]]
    gender: Mapped[Optional[str]]
    fabric_type: Mapped[Optional[str]]
    description: Mapped[Optional[str]] = mapped_column(Text)
    occasion: Mapped[Optional[str]]
    active: Mapped[bool] = mapped_column(default=True)
    search_tsv: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    variants: Mapped[List["ProductVariant"]] = relationship(back_populates="product")
    reviews: Mapped[List["Review"]] = relationship(back_populates="product")
    stats: Mapped[Optional["ProductReviewStat"]] = relationship(back_populates="product")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    sku: Mapped[Optional[str]] = mapped_column(unique=True)
    color: Mapped[Optional[str]]
    size: Mapped[Optional[str]]
    base_price: Mapped[Optional[float]] = mapped_column(Numeric)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    product: Mapped["Product"] = relationship(back_populates="variants")
    images: Mapped[List["ProductImage"]] = relationship(back_populates="variant")
    inventory_global: Mapped["GlobalInventory"] = relationship(uselist=False, back_populates="variant")
    embeddings: Mapped[List["ProductMultimodalEmbedding"]] = relationship(back_populates="variant")
    affinity_a = relationship(
    "ProductAffinity",
    foreign_keys="ProductAffinity.product_variant_id_a",
    back_populates="variant_a"
)

    affinity_b = relationship(
    "ProductAffinity",
    foreign_keys="ProductAffinity.product_variant_id_b",
    back_populates="variant_b"
)

class ProductImage(Base):
    __tablename__ = "product_images"
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), primary_key=True)
    image_url: Mapped[Optional[str]]
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    variant: Mapped["ProductVariant"] = relationship(back_populates="images")

class ProductMultimodalEmbedding(Base):
    __tablename__ = "product_multimodal_embeddings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"))
    modality: Mapped[db_enums.EmbeddingModalityEnum]
    source: Mapped[str]
    embedding: Mapped[List[float]] = mapped_column(Vector(768))
    model: Mapped[str] = mapped_column(default='nomic-embed-v1.5')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    variant: Mapped["ProductVariant"] = relationship(back_populates="embeddings")

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id"))
    rating: Mapped[int]
    comment: Mapped[Optional[str]] = mapped_column(Text)
    images: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship(back_populates="reviews")

class ProductReviewStat(Base):
    __tablename__ = "product_review_stats"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), primary_key=True)
    review_count: Mapped[Optional[int]]
    avg_rating: Mapped[Optional[float]] = mapped_column(Numeric)
    rating_1: Mapped[Optional[int]]
    rating_2: Mapped[Optional[int]]
    rating_3: Mapped[Optional[int]]
    rating_4: Mapped[Optional[int]]
    rating_5: Mapped[Optional[int]]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="stats")

class ReviewSentimentCache(Base):
    __tablename__ = "review_sentiment_cache"
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id"), primary_key=True)
    sentiment: Mapped[Optional[db_enums.ReviewSentimentEnum]]
    confidence: Mapped[Optional[float]] = mapped_column(Numeric)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# ==========================================
# 4. INVENTORY & STORES
# ==========================================

class Store(Base):
    __tablename__ = "stores"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[Optional[str]]
    city: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    address: Mapped[Optional[str]]
    location: Mapped[str] = mapped_column(Geography('POINT', srid=4326))
    opens_at: Mapped[time] = mapped_column(default=time(10, 0))
    closes_at: Mapped[time] = mapped_column(default=time(22, 0))
    active: Mapped[bool] = mapped_column(default=True)
    is_open: Mapped[bool] = mapped_column(default=True)

class GlobalInventory(Base):
    __tablename__ = "global_inventory"
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), primary_key=True)
    total_stock: Mapped[int]
    reserved_stock: Mapped[int]
    assigned_stock: Mapped[int]
    
    variant: Mapped["ProductVariant"] = relationship(back_populates="inventory_global")

class StoreInventory(Base):
    __tablename__ = "store_inventory"
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), primary_key=True)
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), primary_key=True)
    in_stock: Mapped[int]
    reserved_for_pickup: Mapped[int]

class StoreInventoryThreshold(Base):
    __tablename__ = "store_inventory_thresholds"
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), primary_key=True)
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), primary_key=True)
    low_stock_threshold: Mapped[int] = mapped_column(default=5)

class Kiosk(Base):
    __tablename__ = "kiosks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"))
    name: Mapped[Optional[str]]
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    store: Mapped["Store"] = relationship()

# ==========================================
# 5. COMMERCE
# ==========================================

class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="carts")
    items: Mapped[List["CartItem"]] = relationship(back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"
    cart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carts.id"), primary_key=True)
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), primary_key=True)
    quantity: Mapped[int]
    
    cart: Mapped["Cart"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship()

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    fulfillment_type: Mapped[Optional[db_enums.FulfillmentTypeEnum]]
    store_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("stores.id"))
    delivery_address_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    ForeignKey("user_addresses.id")
)
    delivery_address: Mapped[Optional[str]] = mapped_column(Text)
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("agent_runs.id")
    )

    order_status: Mapped[Optional[db_enums.OrderStatusEnum]]
    mutability_state: Mapped[db_enums.OrderMutabilityEnum] = mapped_column(default=db_enums.OrderMutabilityEnum.mutable)
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    feedback_requested: Mapped[bool] = mapped_column(default=False)
    fulfillment_attempts: Mapped[List["FulfillmentAttempt"]] = relationship(back_populates="order")

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order")
    status_history: Mapped[List["OrderStatusHistory"]] = relationship(back_populates="order")
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="order")
    pickup: Mapped[Optional["Pickup"]] = relationship(back_populates="order")
    shipment: Mapped[Optional["Shipment"]] = relationship(back_populates="order")
    change_requests: Mapped[List["OrderChangeRequest"]] = relationship(back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    product_variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), primary_key=True)
    quantity: Mapped[int]
    price_at_purchase: Mapped[float] = mapped_column(Numeric)
    
    order: Mapped["Order"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship()

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    status: Mapped[db_enums.OrderStatusEnum]
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    order: Mapped["Order"] = relationship(back_populates="status_history")

class OrderChangeRequest(Base):
    __tablename__ = "order_change_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    change_type: Mapped[db_enums.OrderChangeTypeEnum]
    change_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[db_enums.OrderChangeStatusEnum] = mapped_column(default=db_enums.OrderChangeStatusEnum.requested)
    decided_by: Mapped[Optional[str]]
    decision_reason: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    order: Mapped["Order"] = relationship(back_populates="change_requests")

class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    cart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carts.id"))
    state: Mapped[db_enums.CheckoutStateEnum]
    locked_price: Mapped[Optional[float]] = mapped_column(Numeric)
    reserved_until: Mapped[Optional[datetime]]
    inventory_locked: Mapped[bool] = mapped_column(default=False)
    payment_attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    session: Mapped["UserSession"] = relationship(back_populates="checkouts")
    user: Mapped["User"] = relationship()
    cart: Mapped["Cart"] = relationship()

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    checkout_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("checkout_sessions.id"))
    method: Mapped[Optional[str]]
    status: Mapped[db_enums.PaymentStatusEnum]
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    idempotency_key: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("agent_runs.id")
    )
    
    order: Mapped["Order"] = relationship(back_populates="payment")
    __table_args__ = (UniqueConstraint("checkout_id", "idempotency_key", name="uq_payment_idempotency"),)

class PaymentGatewayConfig(Base):
    __tablename__ = "payment_gateway_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    force_status: Mapped[Optional[str]]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# ==========================================
# 6. LOGISTICS
# ==========================================

class Pickup(Base):
    __tablename__ = "pickups"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"))
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[db_enums.PickupStatusEnum] = mapped_column(default=db_enums.PickupStatusEnum.pending)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    order: Mapped["Order"] = relationship(back_populates="pickup")

class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    carrier: Mapped[Optional[str]]
    tracking_number: Mapped[Optional[str]]
    status: Mapped[db_enums.ShipmentStatusEnum]
    estimated_delivery: Mapped[Optional[datetime]]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    order: Mapped["Order"] = relationship(back_populates="shipment")

class Return(Base):
    __tablename__ = "returns"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    product_variant_id: Mapped[uuid.UUID]
    quantity: Mapped[int]
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[db_enums.ReturnStatusEnum]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("agent_runs.id")
    )

class Exchange(Base):
    __tablename__ = "exchanges"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    old_variant_id: Mapped[uuid.UUID]
    new_variant_id: Mapped[uuid.UUID]
    status: Mapped[db_enums.ExchangeStatusEnum]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("agent_runs.id")
    )

class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))
    status: Mapped[db_enums.ComplaintStatusEnum] = mapped_column(default=db_enums.ComplaintStatusEnum.open)
    category: Mapped[Optional[str]]
    description: Mapped[Optional[str]] = mapped_column(Text)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolved_by_type: Mapped[Optional[db_enums.ComplaintResolverEnum]]
    resolved_by_id: Mapped[Optional[uuid.UUID]]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# ==========================================
# 7. GROWTH & AGENTS
# ==========================================

class Coupon(Base):
    __tablename__ = "coupons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[Optional[str]]
    coupon_type: Mapped[db_enums.CouponTypeEnum]
    value: Mapped[float] = mapped_column(Numeric)
    scope: Mapped[db_enums.CouponScopeEnum]
    scope_value: Mapped[Optional[str]]
    min_order_value: Mapped[Optional[float]] = mapped_column(Numeric)
    max_discount: Mapped[Optional[float]] = mapped_column(Numeric)
    usage_limit: Mapped[Optional[int]]
    per_user_limit: Mapped[Optional[int]]
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[db_enums.CouponStatusEnum] = mapped_column(default=db_enums.CouponStatusEnum.active)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coupons.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    coupon: Mapped["Coupon"] = relationship()
    __table_args__ = (UniqueConstraint("coupon_id", "order_id"),)

class Event(Base):
    __tablename__ = "events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))
    channel: Mapped[Optional[db_enums.ChannelEnum]]
    event_type: Mapped[db_enums.EventTypeEnum]
    entity_type: Mapped[Optional[db_enums.EntityTypeEnum]]
    entity_id: Mapped[Optional[uuid.UUID]]
    quantity: Mapped[Optional[int]]
    price: Mapped[Optional[float]] = mapped_column(Numeric)
    anonymous_id: Mapped[Optional[uuid.UUID]]
    # FIX: Renamed attribute to prevent collision with SQLAlchemy 'metadata'
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("event_metadata", JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    session: Mapped["UserSession"] = relationship(back_populates="events")

class UserEngagementEvent(Base):
    __tablename__ = "user_engagement_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))

    entity_type: Mapped[db_enums.EntityTypeEnum]
    entity_id: Mapped[uuid.UUID]

    channel: Mapped[db_enums.DeliveryChannelEnum]
    feed: Mapped[Optional[db_enums.RecommendationFeedEnum]]

    state: Mapped[db_enums.EngagementStateEnum]

    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    interacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agent_runs.id"))
    decision_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("decision_records.id"))

    event_metadata_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata", JSONB
    )

class EngagementFollowup(Base):
    __tablename__ = "engagement_followups"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_engagement_events.id", ondelete="CASCADE"))
    followup_reason: Mapped[db_enums.FollowupReasonEnum]
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    executed_by: Mapped[Optional[str]]
    status: Mapped[Optional[str]]
    error_message: Mapped[Optional[str]] = mapped_column(Text)

class OutboundMessage(Base):
    __tablename__ = "outbound_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))

    channel: Mapped[db_enums.DeliveryChannelEnum]

    external_message_id: Mapped[Optional[str]]

    engagement_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_engagement_events.id")
    )

    message_type: Mapped[Optional[str]]
    content: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[db_enums.OutboundMessageStatusEnum]

    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[Optional[uuid.UUID]]
    user_id: Mapped[Optional[uuid.UUID]]
    agent_name: Mapped[Optional[str]]
    agent_role: Mapped[Optional[str]]
    trigger_event: Mapped[Optional[str]]
    status: Mapped[Optional[str]]
    confidence: Mapped[Optional[float]] = mapped_column(Numeric)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # FIX: Renamed attribute to prevent collision with SQLAlchemy 'metadata'
    run_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONB)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class DecisionRecord(Base):
    __tablename__ = "decision_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[Optional[uuid.UUID]]
    user_id: Mapped[Optional[uuid.UUID]]
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agent_runs.id"))
    decision_type: Mapped[Optional[str]]
    decision_output: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric)
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserImageEmbedding(Base):
    __tablename__ = "user_image_embeddings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))
    image_url: Mapped[Optional[str]]
    embedding: Mapped[List[float]] = mapped_column(Vector(768))
    used_for: Mapped[Optional[db_enums.RecommendationFeedEnum]]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RecommendationImpression(Base):
    __tablename__ = "recommendation_impressions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]]
    session_id: Mapped[Optional[uuid.UUID]]
    product_variant_id: Mapped[Optional[uuid.UUID]]
    feed: Mapped[Optional[db_enums.RecommendationFeedEnum]]
    rank_position: Mapped[Optional[int]]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RecommendationOutcome(Base):
    __tablename__ = "recommendation_outcomes"

    impression_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recommendation_impressions.id"),
        primary_key=True
    )
    outcome_type: Mapped[Optional[str]]
    reward: Mapped[Optional[float]] = mapped_column(Numeric)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class TrainingSignal(Base):
    __tablename__ = "training_signals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]]
    product_variant_id: Mapped[Optional[uuid.UUID]]
    signal_type: Mapped[Optional[str]]
    signal_strength: Mapped[Optional[float]] = mapped_column(Numeric)
    source: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    impression_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    ForeignKey("recommendation_impressions.id")
)


class ProductSalesFact(Base):
    __tablename__ = "product_sales_facts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_variant_id: Mapped[Optional[uuid.UUID]]
    order_id: Mapped[Optional[uuid.UUID]]
    event_type: Mapped[Optional[db_enums.ProductSalesEventEnum]]
    quantity: Mapped[Optional[int]]
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ProductMonthlyStats(Base):
    __tablename__ = "product_monthly_stats"
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("product_variants.id", ondelete="CASCADE"),
    primary_key=True
)
    year: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[int] = mapped_column(primary_key=True)
    units_sold: Mapped[Optional[int]]
    units_returned: Mapped[Optional[int]]
    net_units: Mapped[Optional[int]]
    gross_revenue: Mapped[Optional[float]] = mapped_column(Numeric)
    net_revenue: Mapped[Optional[float]] = mapped_column(Numeric)
    order_count: Mapped[Optional[int]]
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
class TrendingProduct(Base):
    __tablename__ = "trending_products"

    scope: Mapped[db_enums.TrendingScopeEnum]
    scope_value: Mapped[str]

    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE")
    )

    rank_position: Mapped[int]
    trending_score: Mapped[float] = mapped_column(Numeric)

    year: Mapped[int]
    month: Mapped[int]

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    variant: Mapped["ProductVariant"] = relationship(
        "ProductVariant",
        lazy="joined",
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "scope",
            "scope_value",
            "product_variant_id",
            "year",
            "month",
            name="pk_trending_products",
        ),
    )

class UserPreferenceSummary(Base):
    __tablename__ = "user_preference_summary"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    summary_text: Mapped[Optional[str]] = mapped_column(Text)
    embedding: Mapped[List[float]] = mapped_column(Vector(768))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
class ModelTrainingRun(Base):
    __tablename__ = "model_training_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[Optional[str]]
    trigger_source: Mapped[Optional[str]]
    training_window_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    training_window_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[Optional[db_enums.TrainingRunStatusEnum]]
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class OrderChangeApplication(Base):
    __tablename__ = "order_change_applications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    change_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("order_change_requests.id"))
    applied_by: Mapped[Optional[str]]
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    snapshot_before: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    snapshot_after: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    
# ==========================================
# 8. LOYALTY & RETENTION (NEW)
# ==========================================

class LoyaltyLedger(Base):
    __tablename__ = "loyalty_ledger"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    transaction_type: Mapped[db_enums.LoyaltyTransactionTypeEnum]
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id"))
    reference_note: Mapped[Optional[str]] = mapped_column(Text)
    
    points: Mapped[int]
    balance_snapshot: Mapped[Optional[int]]
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="loyalty_history")
    order: Mapped["Order"] = relationship()


class ProductAffinity(Base):
    __tablename__ = "product_affinities"

    product_variant_id_a = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        primary_key=True
    )
    product_variant_id_b = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        primary_key=True
    )

    score = mapped_column(Numeric)
    context_scope = mapped_column(String, primary_key=True, default="global")

    variant_a = relationship(
        "ProductVariant",
        foreign_keys=[product_variant_id_a],
        back_populates="affinity_a"
    )

    variant_b = relationship(
        "ProductVariant",
        foreign_keys=[product_variant_id_b],
        back_populates="affinity_b"
    )

class UserPersonalizedOffer(Base):
    __tablename__ = "user_personalized_offers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agent_runs.id"))
    
    offer_name: Mapped[Optional[str]]
    discount_type: Mapped[db_enums.CouponTypeEnum]
    discount_value: Mapped[float] = mapped_column(Numeric)
    condition_text: Mapped[Optional[str]]
    
    is_redeemed: Mapped[bool] = mapped_column(default=False)
    redeemed_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="personalized_offers")


class ProductDiscountRule(Base):
    __tablename__ = "product_discount_rules"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    discount_type: Mapped[db_enums.CouponTypeEnum]
    value: Mapped[float] = mapped_column(Numeric)
    
    category_filter: Mapped[Optional[str]]
    brand_filter: Mapped[Optional[str]]
    product_ids_filter: Mapped[Optional[List[uuid.UUID]]] = mapped_column(ARRAY(UUID))
    
    active: Mapped[bool] = mapped_column(default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentHandoff(Base):
    __tablename__ = "agent_handoffs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.id"))

    # customer who triggered handoff
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))

    # admin assigned
    assigned_to_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))

    from_agent_name: Mapped[Optional[str]]
    reason: Mapped[Optional[str]]
    summary: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[db_enums.ComplaintStatusEnum] = mapped_column(default=db_enums.ComplaintStatusEnum.open)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ✅ clarify relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="agent_handoffs",
    )

    assigned_admin: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_to_admin_id],
    )


class FulfillmentAttempt(Base):
    __tablename__ = "fulfillment_attempts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    
    attempt_number: Mapped[int] = mapped_column(default=1)
    max_retries: Mapped[int] = mapped_column(default=5)
    attempt_type: Mapped[Optional[db_enums.FulfillmentTypeEnum]]
    
    status: Mapped[Optional[str]]
    last_error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agent_runs.id"))
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    order: Mapped["Order"] = relationship(back_populates="fulfillment_attempts")
    
    
class UserAddress(Base):
    __tablename__ = "user_addresses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    name: Mapped[str]
    phone: Mapped[str]
    address_line: Mapped[str] = mapped_column(Text)
    city: Mapped[str]
    state: Mapped[str]
    pincode: Mapped[str]
    type: Mapped[str] = mapped_column(default="home") # 'home' or 'work'
    is_default: Mapped[bool] = mapped_column(default=False)
    
    # PostGIS Location for fast distance querying
    location: Mapped[Optional[str]] = mapped_column(Geography('POINT', srid=4326))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="addresses")
    
    


# IMPORTANT: In your User class inside models.py, add this line:
# addresses: Mapped[List["UserAddress"]] = relationship(back_populates="user")


class CouponEmbedding(Base):
    __tablename__ = "coupon_embeddings"

    coupon_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("coupons.id", ondelete="CASCADE"),
        primary_key=True
    )
    embedding: Mapped[List[float]] = mapped_column(Vector(768))
    model: Mapped[str] = mapped_column(default="nomic-embed-text-v1.5")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class UserPersonalizedOfferEmbedding(Base):
    __tablename__ = "user_personalized_offer_embeddings"

    offer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_personalized_offers.id", ondelete="CASCADE"),
        primary_key=True
    )
    embedding: Mapped[List[float]] = mapped_column(Vector(768))
    model: Mapped[str] = mapped_column(default="nomic-embed-text-v1.5")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
class ProductPriceSnapshot(Base):
    __tablename__ = "product_price_snapshots"

    product_variant_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id"),
        primary_key=True
    )
    base_price = mapped_column(Numeric, nullable=False)
    display_price = mapped_column(Numeric, nullable=False)
    discount_percent = mapped_column(Numeric)
    discount_reason = mapped_column(Text)
    computed_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    valid_until = mapped_column(DateTime(timezone=True))



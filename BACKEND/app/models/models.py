# app/models/modeles.py
import uuid
from sqlalchemy import (
    Column, String, Boolean, ForeignKey, Numeric, Integer, Text, DateTime, 
    ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy import Enum as SAEnum
from app.enums import db_enums


from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base  # Assuming this exists as per your snippet

# Import specific types for advanced Postgres features
from pgvector.sqlalchemy import Vector
from geoalchemy2 import Geography

# ==========================================
# 1. USER & IDENTITY DOMAIN
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    email = Column(String, unique=True)
    phone = Column(String, unique=True)
    loyalty_tier = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(SAEnum(db_enums.UserRoleEnum, name="user_role_enum"), default=db_enums.UserRoleEnum.user)

    # Relationships
    sessions = relationship("Session", back_populates="user")
    orders = relationship("Order", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    cards = relationship("UserCard", back_populates="user")
    preferences = relationship("UserPreferences", uselist=False, back_populates="user")
    preference_summary = relationship("UserPreferenceSummary", uselist=False, back_populates="user")
    whatsapp_info = relationship("WhatsappUser", uselist=False, back_populates="user")
    wishlist = relationship("UserWishlist", back_populates="user")


class UserCard(Base):
    __tablename__ = "user_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    card_name = Column(String)
    card_number = Column(String, unique=True)
    card_expiry = Column(String)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

    user = relationship("User", back_populates="cards")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    preferred_categories = Column(ARRAY(Text))
    preferred_price_min = Column(Numeric)
    preferred_price_max = Column(Numeric)
    preferred_sizes = Column(ARRAY(Text))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")


class UserPreferenceSummary(Base):
    __tablename__ = "user_preference_summary"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    summary_text = Column(Text)
    embedding = Column(Vector(768))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preference_summary")


class UserEmbedding(Base):
    __tablename__ = "user_embeddings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    embedding = Column(Vector(768))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
class UserAddress(Base):
    __tablename__ = "user_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    label = Column(String)
    address_line1 = Column(Text, nullable=False)
    address_line2 = Column(Text)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)
    country = Column(String, default="India")
    location = Column(Geography(geometry_type="POINT", srid=4326))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

class UserWishlist(Base):
    __tablename__ = "user_wishlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="wishlist")
    variant = relationship("ProductVariant")

# ==========================================
# 2. SESSION & CONVERSATION DOMAIN
# ==========================================

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    primary_channel = Column(SAEnum(db_enums.ChannelEnum, name="channel_enum"))
    active_channel = Column(SAEnum(db_enums.ChannelEnum, name="channel_enum"))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session")
    events = relationship("Event", back_populates="session")
    summary = relationship("ConversationSummary", uselist=False, back_populates="session")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    channel = Column(SAEnum(db_enums.ChannelEnum, name="channel_enum"))
    speaker = Column(String)
    message = Column(Text)
    intent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="conversations")


class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), primary_key=True)
    summary_text = Column(Text)
    embedding = Column(Vector(768))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="summary")


class UserIntent(Base):
    __tablename__ = "user_intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    intent_text = Column(Text)
    intent_category = Column(Text)
    confidence = Column(Numeric)
    # TSVECTOR is supported in newer SQLAlchemy versions, otherwise treat as specialized type
    intent_tsv = Column(TSVECTOR) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==========================================
# 3. PRODUCT & CATALOG DOMAIN
# ==========================================

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand = Column(String)
    category = Column(String)
    gender = Column(String)
    fabric_type = Column(String)
    description = Column(Text)
    occasion = Column(String)
    active = Column(Boolean, default=True)
    reviews = relationship("Review", back_populates="product")

    variants = relationship("ProductVariant", back_populates="product")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    rating = Column(Integer)
    comment = Column(Text)
    images = Column(ARRAY(Text)) # Optional: User uploaded photos
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    product = relationship("Product", back_populates="reviews")
class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    sku = Column(String, unique=True)
    color = Column(String)
    size = Column(String)
    base_price = Column(Numeric)
    active = Column(Boolean, default=True)

    product = relationship("Product", back_populates="variants")
    images = relationship("ProductImage", back_populates="variant")
    inventory_global = relationship("GlobalInventory", uselist=False, back_populates="variant")
    embedding = relationship("ProductEmbedding", uselist=False, back_populates="variant")


class ProductImage(Base):
    __tablename__ = "product_images"

    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), primary_key=True)
    image_url = Column(String)
    position = Column(Integer, primary_key=True)

    variant = relationship("ProductVariant", back_populates="images")


class ProductEmbedding(Base):
    __tablename__ = "product_embeddings"

    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), primary_key=True)
    embedding = Column(Vector(768))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    variant = relationship("ProductVariant", back_populates="embedding")


class CategoryTrending(Base):
    __tablename__ = "category_trending"

    category = Column(String, primary_key=True)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    rank_position = Column(Integer, primary_key=True)
    computed_at = Column(DateTime(timezone=True))


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    min_cart_value = Column(Numeric)
    max_discount_amount = Column(Numeric)
    discount_type = Column(String)
    discount_value = Column(Numeric)
    eligible_category = Column(String)
    stackable = Column(Boolean)
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))
    active = Column(Boolean)


# ==========================================
# 4. STORE & INVENTORY DOMAIN
# ==========================================

class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    city = Column(String)
    state = Column(String)
    address = Column(String)
    # Using GeoAlchemy2 for Geography type
    location = Column(Geography(geometry_type='POINT', srid=4326))
    active = Column(Boolean, default=True)


class GlobalInventory(Base):
    __tablename__ = "global_inventory"

    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), primary_key=True)
    total_stock = Column(Integer)
    reserved_stock = Column(Integer)
    assigned_stock = Column(Integer)

    variant = relationship("ProductVariant", back_populates="inventory_global")


class StoreInventory(Base):
    __tablename__ = "store_inventory"

    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), primary_key=True)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), primary_key=True)
    in_stock = Column(Integer)
    reserved_for_pickup = Column(Integer)


# ==========================================
# 5. ORDER & CART DOMAIN
# ==========================================

class Cart(Base):
    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), primary_key=True)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), primary_key=True)
    quantity = Column(Integer)

    cart = relationship("Cart", back_populates="items")
    variant = relationship("ProductVariant")


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    fulfillment_type = Column(SAEnum(db_enums.FulfillmentTypeEnum, name="fulfillment_type_enum"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    delivery_address = Column(Text)
    order_status = Column(SAEnum(db_enums.OrderStatusEnum, name="order_status_enum"))
    total_amount = Column(Numeric)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    status_history = relationship("OrderStatusHistory", back_populates="order")
    payment = relationship("Payment", uselist=False, back_populates="order")
    pickup = relationship("Pickup", uselist=False, back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), primary_key=True)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), primary_key=True)
    quantity = Column(Integer)
    price_at_purchase = Column(Numeric)

    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    status = Column(SAEnum(db_enums.OrderStatusEnum, name="order_status_enum"))
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="status_history")



class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    method = Column(String)
    status = Column(SAEnum(db_enums.PaymentStatusEnum, name="payment_status_enum"))
    failure_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payment")


class Pickup(Base):
    __tablename__ = "pickups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    scheduled_time = Column(DateTime(timezone=True))
    scheduled_day = Column(String)
    status = Column(SAEnum(db_enums.PickupStatusEnum, name="pickup_status_enum"), default=db_enums.PickupStatusEnum.pending)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="pickup")


# ==========================================
# 6. ANALYTICS & EXTERNAL CHANNELS
# ==========================================

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    channel = Column(SAEnum(db_enums.ChannelEnum, name="channel_enum"))
    event_type = Column(SAEnum(db_enums.EventTypeEnum, name="event_type_enum"))
    entity_type = Column(SAEnum(db_enums.EntityTypeEnum, name="entity_type_enum"))
    entity_id = Column(UUID(as_uuid=True))
    quantity = Column(Integer)
    price = Column(Numeric)
    reason = Column(Text)
    event_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="events")


class WhatsappUser(Base):
    __tablename__ = "whatsapp_users"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    whatsapp_number = Column(String)
    opt_in = Column(Boolean)

    user = relationship("User", back_populates="whatsapp_info")


class WhatsappMessage(Base):
    __tablename__ = "whatsapp_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    direction = Column(String)
    message = Column(Text)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    status = Column(String, default='open')
    category = Column(String)
    description = Column(Text)
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    order = relationship("Order")
    
    
class RecommendationImpression(Base):
    __tablename__ = "recommendation_impressions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    feed_type = Column(String)
    rank_position = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecommendationOutcome(Base):
    __tablename__ = "recommendation_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    impression_id = Column(UUID(as_uuid=True), ForeignKey("recommendation_impressions.id"))
    outcome_type = Column(String)
    reward_value = Column(Numeric)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    
class OfferEmbedding(Base):
    __tablename__ = "offer_embeddings"
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(Vector(768))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    
class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    points = Column(Integer, nullable=False)
    source = Column(String)  # order, return, promo
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    carrier = Column(Text)
    tracking_number = Column(Text)

    status = Column(
    SAEnum(db_enums.ShipmentStatusEnum, name="shipment_status_enum"),
    nullable=False
)

    estimated_delivery = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Return(Base):
    __tablename__ = "returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_variant_id = Column(UUID(as_uuid=True))
    quantity = Column(Integer)
    reason = Column(Text)

    status = Column(SAEnum(db_enums.ReturnStatusEnum, name="return_status_enum"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
class Exchange(Base):
    __tablename__ = "exchanges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    old_variant_id = Column(UUID(as_uuid=True))
    new_variant_id = Column(UUID(as_uuid=True))

    status = Column(SAEnum(db_enums.ExchangeStatusEnum, name="exchange_status_enum"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"))

    state = Column(SAEnum(db_enums.CheckoutStateEnum, name="checkout_state_enum"), nullable=False)
    locked_price = Column(Numeric)
    reserved_until = Column(DateTime)

    payment_attempts = Column(Integer, default=0)
    last_error = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
class TelegramUser(Base):
    __tablename__ = "telegram_users"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id = Column(Text, unique=True, nullable=False)
    opt_in = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TelegramMessage(Base):
    __tablename__ = "telegram_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    chat_id = Column(Text, nullable=False)
    direction = Column(Text)  # inbound | outbound
    message = Column(Text)
    status = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
# app/enums/db_enums.py
from enum import Enum

class ChannelEnum(str, Enum):
    web = "web"
    app = "app"
    kiosk = "kiosk"
    whatsapp = "whatsapp"
    telegram = "telegram"

class UserRoleEnum(str, Enum):
    user = "user"
    admin = "admin"

class FulfillmentTypeEnum(str, Enum):
    delivery = "delivery"
    pickup = "pickup"

class OrderStatusEnum(str, Enum):
    created = "created"
    confirmed = "confirmed"
    packed = "packed"
    shipped = "shipped"
    ready_for_pickup = "ready_for_pickup"
    delivered = "delivered"
    cancelled = "cancelled"

class PaymentStatusEnum(str, Enum):
    initiated = "initiated"
    success = "success"
    failed = "failed"
    abandoned = "abandoned"

class PickupStatusEnum(str, Enum):
    pending = "pending"
    ready_for_pickup = "ready_for_pickup"
    picked_up = "picked_up"
    cancelled = "cancelled"

class CheckoutStateEnum(str, Enum):
    INIT = "INIT"
    CART_VALIDATED = "CART_VALIDATED"
    STOCK_RESERVED = "STOCK_RESERVED"
    PRICE_LOCKED = "PRICE_LOCKED"
    COUPON_APPLIED = "COUPON_APPLIED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    DELIVERY_SCHEDULED = "DELIVERY_SCHEDULED"
    ORDER_CONFIRMED = "ORDER_CONFIRMED"
    ROLLED_BACK = "ROLLED_BACK"

class EventTypeEnum(str, Enum):
    product_view = "product_view"
    search = "search"
    add_to_cart = "add_to_cart"
    remove_from_cart = "remove_from_cart"
    wishlist_add = "wishlist_add"
    checkout_started = "checkout_started"
    checkout_cancelled = "checkout_cancelled"
    payment_started = "payment_started"
    payment_failed = "payment_failed"
    payment_success = "payment_success"
    order_placed = "order_placed"
    pickup_selected = "pickup_selected"
    delivery_selected = "delivery_selected"
    session_started = "session_started"


class EntityTypeEnum(str, Enum):
    product = "product"
    product_variant = "product_variant"
    cart = "cart"
    order = "order"
    offer = "offer"
    checkout = "checkout"
    user_session = "user_session"


class ExchangeStatusEnum(str, Enum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"
    cancelled = "cancelled"

class ReturnStatusEnum(str, Enum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    picked_up = "picked_up"
    refunded = "refunded"
    cancelled = "cancelled"

class ShipmentStatusEnum(str, Enum):
    created = "created"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    delayed = "delayed"
    cancelled = "cancelled"

class TrendingScopeEnum(str, Enum):
    global_ = "global"   # underscore to avoid keyword clash
    category = "category"
    brand = "brand"



class RecommendationFeedEnum(str, Enum):
    home = "home"
    search = "search"
    similar = "similar"
    image_search = "image_search"
    trending = "trending"

class ReviewSentimentEnum(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class ProductSalesEventEnum(str, Enum):
    sale = "sale"
    return_ = "return"
    exchange_out = "exchange_out"
    exchange_in = "exchange_in"

class EmbeddingModalityEnum(str, Enum):
    text = "text"
    image = "image"

class TrainingRunStatusEnum(str, Enum):
    started = "started"
    completed = "completed"
    failed = "failed"

class CardBrandEnum(str, Enum):
    visa = "visa"
    mastercard = "mastercard"
    rupay = "rupay"
    amex = "amex"
    other = "other"

class KioskStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"

# --- COUPONS ---
class CouponTypeEnum(str, Enum):
    percentage = "percentage"
    flat = "flat"

class CouponStatusEnum(str, Enum):
    active = "active"
    expired = "expired"
    disabled = "disabled"

class CouponScopeEnum(str, Enum):
    global_ = "global"
    category = "category"
    product = "product"

# --- ORDER MUTABILITY ---
class OrderMutabilityEnum(str, Enum):
    mutable = "mutable"
    locked = "locked"
    shipped = "shipped"

class OrderChangeTypeEnum(str, Enum):
    add_item = "add_item"
    remove_item = "remove_item"
    change_quantity = "change_quantity"
    change_address = "change_address"
    cancel_order = "cancel_order"

class OrderChangeStatusEnum(str, Enum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"

# --- COMPLAINTS ---
class ComplaintStatusEnum(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class ComplaintResolverEnum(str, Enum):
    agent = "agent"
    admin = "admin"

# --- ENGAGEMENT ---
class DeliveryChannelEnum(str, Enum):
    in_app = "in_app"
    telegram = "telegram"
    whatsapp = "whatsapp"
    email = "email"

class EngagementStateEnum(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    unopened = "unopened"
    opened = "opened"
    clicked = "clicked"
    ignored = "ignored"
    dismissed = "dismissed"
    converted = "converted"
class OutboundMessageStatusEnum(str, Enum):
    pending = "pending"   # created, not yet sent
    sent = "sent"         # provider accepted / delivered
    failed = "failed"     # provider rejected / network error


class FollowupReasonEnum(str, Enum):
    no_open = "no_open"
    no_click = "no_click"
    price_drop = "price_drop"
    inventory_low = "inventory_low"
    pickup_reminder = "pickup_reminder"
    delivery_failed = "delivery_failed"
    agent_retry = "agent_retry"
    
    
    
# --- LOYALTY (New) ---
class LoyaltyTransactionTypeEnum(str, Enum):
    earned_purchase = "earned_purchase"
    earned_bonus = "earned_bonus"
    redeemed_checkout = "redeemed_checkout"
    expired = "expired"
    admin_adjustment = "admin_adjustment"
    refund_reversal = "refund_reversal"
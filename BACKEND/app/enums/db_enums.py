# app/enums/db_enums.py
from enum import Enum

class ChannelEnum(str, Enum):
    web = "web"
    app = "app"
    kiosk = "kiosk"
    whatsapp = "whatsapp"

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

class EventTypeEnum(str, Enum):
    product_view = "product_view"
    search = "search"
    add_to_cart = "add_to_cart"
    remove_from_cart = "remove_from_cart"
    checkout_started = "checkout_started"
    checkout_cancelled = "checkout_cancelled"
    payment_started = "payment_started"
    payment_failed = "payment_failed"
    payment_success = "payment_success"
    order_placed = "order_placed"
    pickup_selected = "pickup_selected"
    delivery_selected = "delivery_selected"

class EntityTypeEnum(str, Enum):
    product = "product"
    product_variant = "product_variant"
    cart = "cart"
    order = "order"

class PickupStatusEnum(str, Enum):
    pending = "pending"
    ready_for_pickup = "ready_for_pickup"
    picked_up = "picked_up"
    cancelled = "cancelled"

class PaymentStatusEnum(str, Enum):
    initiated = "initiated"
    success = "success"
    failed = "failed"
    abandoned = "abandoned"
    
    
class UserRoleEnum(str, Enum):
    user = "user"
    admin = "admin"
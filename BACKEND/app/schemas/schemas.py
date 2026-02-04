# app/schemas/schemas.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict, Any
from app.enums.db_enums import OrderStatusEnum, PickupStatusEnum
from datetime import datetime


# ---------------- PRODUCTS ----------------

class ProductCreate(BaseModel):
    brand: str
    category: str
    gender: Optional[str]
    fabric_type: Optional[str]
    description: Optional[str]
    occasion: Optional[str]

class ProductUpdate(ProductCreate):
    active: Optional[bool]

class VariantCreate(BaseModel):
    product_id: UUID
    sku: str
    color: str
    size: str
    base_price: float

class VariantUpdate(BaseModel):
    color: Optional[str]
    size: Optional[str]
    base_price: Optional[float]
    active: Optional[bool]

class VariantImageCreate(BaseModel):
    image_url: str
    position: int

# ---------------- STORES ----------------

class StoreCreate(BaseModel):
    name: str
    city: str
    state: str
    address: str
    location: Dict[str, Any]  # GeoJSON Point

class StoreUpdate(BaseModel):
    name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    address: Optional[str]
    active: Optional[bool]
    location: Optional[Dict[str, Any]]
    
    
    

class StoreResponse(BaseModel):
    id: UUID
    name: str
    city: str
    state: str
    address: str
    location: Dict[str, Any]

    class Config:
        orm_mode = True


# ---------------- INVENTORY ----------------

class AssignGlobalInventory(BaseModel):
    product_variant_id: UUID
    quantity: int

class AssignStoreInventory(BaseModel):
    store_id: UUID
    product_variant_id: UUID
    quantity: int

# ---------------- PICKUPS ----------------

class PickupStatusUpdate(BaseModel):
    status: PickupStatusEnum
    
# --- COMPLAINTS SCHEMAS (Added) ---
class ComplaintCreate(BaseModel):
    user_id: UUID
    order_id: Optional[UUID]
    session_id: Optional[UUID]
    category: str
    description: str

class ComplaintStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str]

# --- OFFERS (Refined) ---
class OfferCreate(BaseModel):
    name: str
    min_cart_value: float
    max_discount_amount: float
    discount_type: str
    discount_value: float
    eligible_category: Optional[str]
    stackable: bool
    valid_from: str # ISO Date string
    valid_to: str   # ISO Date string
    active: bool

class OfferUpdate(OfferCreate):
    pass

# ---------------- DELIVERY ----------------

class OrderStatusUpdate(BaseModel):
    status: OrderStatusEnum
    description: Optional[str]

# ---------------- COMPLAINTS ----------------

class ComplaintStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str]

# ---------- ADDRESSES ----------

class AddressCreate(BaseModel):
    label: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    pincode: str
    country: Optional[str] = "India"
    location: Optional[Dict[str, Any]]  # GeoJSON Point
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    country: Optional[str]
    location: Optional[Dict[str, Any]]
    is_default: Optional[bool]


# ---------- WISHLIST ----------

class WishlistAdd(BaseModel):
    product_variant_id: UUID


# ---------- CART ----------

class CartItemAdd(BaseModel):
    product_variant_id: UUID
    quantity: int


class CartItemUpdate(BaseModel):
    quantity: int


# ---------- SEARCH ----------

class SearchQuery(BaseModel):
    query: str
    channel: str  # web/app/kiosk/whatsapp
    
    
class ReviewCreate(BaseModel):
    product_id: UUID
    rating: int
    comment: Optional[str] = None
    images: Optional[List[str]] = []

class ReviewResponse(BaseModel):
    id: UUID
    user_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    
class LoyaltyEarn(BaseModel):
    order_id: UUID
    points: int


class ShipmentCreate(BaseModel):
    order_id: UUID
    carrier: str
    tracking_number: str
    estimated_delivery: datetime

class ReturnCreate(BaseModel):
    order_id: UUID
    product_variant_id: UUID
    quantity: int
    reason: str

class ExchangeCreate(BaseModel):
    order_id: UUID
    old_variant_id: UUID
    new_variant_id: UUID
class PersonalizedOffer(BaseModel):
    variant_id: UUID
    discount_percent: int
    reason: str
class UserRegisterPayload(BaseModel):
    name: str
    phone: Optional[str] = None

from app.enums.db_enums import ChannelEnum

class SessionStartResponse(BaseModel):
    session_id: UUID
    primary_channel: ChannelEnum
    active_channel: ChannelEnum
    started_at: datetime

class SessionActiveResponse(SessionStartResponse):
    pass

from app.enums.db_enums import CheckoutStateEnum

class CheckoutStartResponse(BaseModel):
    checkout_id: UUID
    state: CheckoutStateEnum
    reserved_until: Optional[datetime]

class CheckoutIntrospection(BaseModel):
    checkout_id: UUID
    state: CheckoutStateEnum
    locked_price: Optional[float]
    reserved_until: Optional[datetime]
    payment_attempts: int
    last_error: Optional[str]
    
from app.enums.db_enums import OrderStatusEnum


class UpdateDeliveryStatusRequest(BaseModel):
    status: OrderStatusEnum
    description: Optional[str] = None
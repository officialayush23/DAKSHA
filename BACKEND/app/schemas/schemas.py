# app/schemas/schemas.py

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.enums.db_enums import (
    CouponStatusEnum, EntityTypeEnum, OrderStatusEnum, ChannelEnum, CheckoutStateEnum,
    FulfillmentTypeEnum, ComplaintStatusEnum,
    CouponTypeEnum, CouponScopeEnum, OrderChangeTypeEnum,
    DeliveryChannelEnum, EngagementStateEnum
)
from pydantic import field_validator
from app.utils.geo import serialize_point
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
class ProductImagePayload(BaseModel):
    image_url: str
# --- USER & PREFERENCES ---
class UserProfileUpdate(BaseSchema):
    name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None

class UserPreferencesUpdate(BaseSchema):
    preferred_categories: Optional[List[str]] = None
    excluded_categories: Optional[List[str]] = None
    preferred_price_min: Optional[Decimal] = None
    preferred_price_max: Optional[Decimal] = None
    preferred_fulfillment: Optional[FulfillmentTypeEnum] = None
    min_acceptable_rating: Optional[Decimal] = None
    preferred_sizes: Optional[List[str]] = None
    preferred_colors: Optional[List[str]] = None

class UserRegisterPayload(BaseSchema):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    
# --- PRODUCT ---
class ProductCreate(BaseSchema):
    brand: str
    category: str
    name: str
    gender: Optional[str] = None
    fabric_type: Optional[str] = None
    description: Optional[str] = None
    occasion: Optional[str] = None

class VariantCreate(BaseSchema):
    product_id: UUID
    sku: str
    color: str
    size: str
    base_price: float

class VariantUpdate(BaseSchema):
    color: Optional[str] = None
    size: Optional[str] = None
    base_price: Optional[float] = None
    active: Optional[bool] = None

# --- STORES ---
class StoreCreate(BaseSchema):
    name: str
    city: str
    state: str
    address: str
    location: Dict[str, Any]


class StoreResponse(BaseSchema):
    id: UUID
    name: str
    location: List[float]

    @field_validator("location", mode="before")
    def parse_location(cls, v):
        return serialize_point(v)
class KioskLoginRequest(BaseSchema):
    phone: str
    kiosk_id: UUID

class KioskLoginResponse(BaseSchema):
    user_id: UUID
    session_id: UUID
    kiosk_id: UUID
    store_id: UUID
    primary_channel: ChannelEnum
    active_channel: ChannelEnum
    name: Optional[str] = None
    phone: Optional[str] = None

# --- INVENTORY ---
class AssignStoreInventory(BaseSchema):
    store_id: UUID
    product_variant_id: UUID
    quantity: int

class InventoryCheckResponse(BaseSchema):
    variant_id: UUID
    store_id: UUID
    available: bool
    quantity: int
    reserved: int

# --- COUPONS ---
class CouponCreate(BaseSchema):
    code: str
    description: Optional[str] = None
    coupon_type: CouponTypeEnum
    value: float
    scope: CouponScopeEnum
    scope_value: Optional[str] = None
    min_order_value: Optional[float] = None
    max_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    per_user_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: Optional[CouponStatusEnum] = CouponStatusEnum.active


class CouponApplyRequest(BaseSchema):
    code: str
    cart_id: UUID

# --- CART & ORDER ---
class CartItemAdd(BaseSchema):
    product_variant_id: UUID
    quantity: int

class OrderCreate(BaseSchema):
    user_id: UUID
    fulfillment_type: FulfillmentTypeEnum
    store_id: Optional[UUID] = None
    delivery_address: Optional[str] = None

class OrderStatusUpdate(BaseSchema):
    status: OrderStatusEnum
    description: Optional[str] = None

class OrderChangeRequestCreate(BaseSchema):
    order_id: UUID
    change_type: OrderChangeTypeEnum
    change_payload: Dict[str, Any]

# --- CHECKOUT ---
class CheckoutStartResponse(BaseSchema):
    checkout_id: UUID
    state: CheckoutStateEnum
    reserved_until: Optional[datetime]

class CheckoutIntrospection(BaseSchema):
    checkout_id: UUID
    state: CheckoutStateEnum
    locked_price: Optional[float]
    payment_attempts: int
    last_error: Optional[str]

# --- COMPLAINTS ---
class ComplaintCreate(BaseSchema):
    user_id: UUID
    order_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    category: str
    description: str

class ComplaintStatusUpdate(BaseSchema):
    status: ComplaintStatusEnum
    resolution_notes: Optional[str] = None

# --- AGENT OBSERVABILITY ---
class EngagementEventTrack(BaseSchema):
    user_id: UUID
    entity_type: EntityTypeEnum
    entity_id: UUID
    channel: DeliveryChannelEnum
    state: EngagementStateEnum
    metadata: Optional[Dict[str, Any]] = None

class AgentRunLog(BaseSchema):
    session_id: UUID
    agent_name: str
    agent_role: str
    trigger_event: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

class DecisionRecordLog(BaseSchema):
    agent_run_id: UUID
    decision_type: str
    decision_output: Dict[str, Any]
    confidence: float
    rationale: str

# --- MESSAGING ---
class OutboundMessageCreate(BaseSchema):
    user_id: UUID
    channel: DeliveryChannelEnum
    message_type: str
    content: str
    engagement_event_id: Optional[UUID] = None

# --- ANALYTICS ---
class RecommendedVariant(BaseSchema):
    variant_id: UUID
    product_id: UUID
    price: float
    discounted_price: Optional[float] = None
    reason: str
    rank: int

class ReviewCreate(BaseSchema):
    product_id: UUID
    rating: int
    comment: Optional[str] = None
    images: Optional[List[str]] = []

class ReviewResponse(BaseSchema):
    id: UUID
    user_name: Optional[str] = "Anonymous"
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    
    
from app.enums.db_enums import LoyaltyTransactionTypeEnum
class LocationInput(BaseModel):
    coordinates: List[float] # [longitude, latitude]

class AddressCreate(BaseSchema):
    label: str | None
    address_line1: str
    address_line2: str | None
    city: str | None
    state: str | None
    pincode: str | None
    type: Optional[str] = "home"
    is_default: Optional[bool] = False

# --- NEW: LOYALTY ---
class LoyaltyLedgerSchema(BaseSchema):
    id: UUID
    transaction_type: LoyaltyTransactionTypeEnum
    points: int
    balance_snapshot: Optional[int]
    reference_note: Optional[str]
    created_at: datetime
class LocationPing(BaseModel):
    lat: float
    lng: float
# --- NEW: PERSONALIZED OFFERS ---
class PersonalizedOfferSchema(BaseSchema):
    id: UUID
    offer_name: Optional[str]
    discount_value: float
    discount_type: CouponTypeEnum
    expires_at: datetime
    is_redeemed: bool

# --- NEW: AGENT HANDOFF ---
class AgentHandoffCreate(BaseSchema):
    session_id: UUID
    reason: str
    summary: str
    from_agent_name: str
    
    
class AddressUpdate(BaseSchema):
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    type: Optional[str] = None
    is_default: Optional[bool] = None

class AddressLocationPatch(BaseSchema):
    lat: float
    lng: float

# --- SEARCH SCHEMA ---
class SearchQuery(BaseSchema):
    query: str
    channel: ChannelEnum = ChannelEnum.web

# --- WISHLIST SCHEMA ---
class WishlistAdd(BaseSchema):
    product_variant_id: UUID

class CartItemUpdate(BaseSchema):
    quantity: int

class CardCreate(BaseSchema):
    card_brand: str # Use Enum in real app
    card_last4: str
    token: str
    card_name: Optional[str] = None
    is_default: bool = False
    

class ReturnRequest(BaseModel):
    order_id: UUID
    product_variant_id: UUID
    quantity: int
    reason: str

    class Config:
        from_attributes = True

class ComplaintRequest(BaseModel):
    order_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    category: str
    description: str

    class Config:
        from_attributes = True

class ComplaintUpdateRequest(BaseModel):
    status: ComplaintStatusEnum
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True

class ExchangeRequest(BaseModel):
    order_id: UUID
    old_variant_id: UUID
    new_variant_id: UUID

    class Config:
        from_attributes = True

class CancelRequest(BaseModel):
    reason: Optional[str] = None

    class Config:
        from_attributes = True

class StatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None

    class Config:
        from_attributes = True    
class AssignGlobalInventory(BaseSchema):
    product_variant_id: UUID
    quantity: int
    
class KioskCreate(BaseSchema):
    store_id: UUID
    name: str

class PickupStatusUpdate(BaseSchema):
    status: str
    scheduled_time: Optional[datetime] = None

class ReturnDecision(BaseSchema):
    approved: bool
    reason: str

class ExchangeDecision(BaseSchema):
    approved: bool
    reason: str

class PickupStatusUpdate(BaseSchema):
    status: str
    scheduled_time: Optional[datetime] = None
class AdminReason(BaseSchema):
    reason: str
class AdminUserListItem(BaseSchema):
    id: UUID
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    created_at: datetime


# app/schemas/schemas.py

class VariantCreateNested(BaseSchema):
    sku: str
    color: str
    size: str
    base_price: float

class ProductCreate(BaseSchema):
    brand: str
    category: str
    name: str
    gender: Optional[str] = None
    fabric_type: Optional[str] = None
    description: Optional[str] = None
    occasion: Optional[str] = None

    # NEW
    variants: List[VariantCreateNested] = []



class ProductDiscountRuleCreate(BaseModel):
    name: str

    discount_type: CouponTypeEnum
    value: float

    category_filter: Optional[str] = None
    brand_filter: Optional[str] = None
    product_ids_filter: Optional[List[UUID]] = None

    active: bool = True
    valid_from: datetime
    valid_to: Optional[datetime] = None

    class Config:
        model_config = ConfigDict(from_attributes=True)
class AgentInventoryView(BaseSchema):
    product_name: str
    variant_sku: str

    global_stock_available: bool
    local_store_id: Optional[UUID]
    local_stock_available: bool

    alternative_stores: List[UUID]
class SessionContext(BaseSchema):
    current_intent: Optional[str] = None
    detected_constraints: Dict[str, Any] = {}
    last_product_viewed: Optional[UUID] = None
    funnel_stage: Optional[str] = None
    confidence: Optional[float] = None
    
    
class ApplyCouponRequest(BaseModel):
    checkout_id: str
    coupon_code: str | None = None
    personal_offer_id: str | None = None
    cart_total: float
    
    
class StoreAvailability(BaseModel):
    store_id: UUID
    name: str
    address: str
    distance_meters: float
    
    
class StoreLookupRequest(BaseModel):
    cart_id: UUID

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    limit: int = Field(default=5, ge=1, le=20)
    
    
class DeliveryCheckoutRequest(BaseModel):
    user_id: UUID
    session_id: UUID
    cart_id: UUID

class PickupCheckoutRequest(BaseModel):
    user_id: UUID
    session_id: UUID
    cart_id: UUID
    store_id: UUID

class FinalizeCheckoutRequest(BaseModel):
    # ⬇️ REMOVED fulfillment_type and store_id
    delivery_address_id: Optional[UUID] = None
    scheduled_time: Optional[str] = None  # Use ISO format for parsing
    redeem_loyalty_points: int = 0

class ApplyCouponPayload(BaseModel):
    coupon_code: Optional[str] = None
    offer_id: Optional[UUID] = None
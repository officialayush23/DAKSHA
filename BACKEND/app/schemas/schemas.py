# app/schemas/schemas.py
"""
Request/Response Schemas - UI-Friendly API DTOs
Separate from database models (app.models.all_models)
"""

from pydantic import BaseModel, Field, constr
from typing import Optional, List, Dict, Any
from datetime import date, datetime


# ============================================================================
# AUTH & USER SCHEMAS
# ============================================================================

class LoginWithPhoneRequest(BaseModel):
    """Phone-based login"""
    phone_number: constr(pattern=r"^\+[1-9]\d{1,14}$")
    guest_id: str


class UserProfileUpdate(BaseModel):
    """User profile update/registration"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_active_at: datetime


class PaymentMethodCreate(BaseModel):
    """Add payment method"""
    gateway_token_id: str
    card_last4: str
    card_brand: str


# ============================================================================
# COMMERCE SCHEMAS
# ============================================================================

class AddToCartRequest(BaseModel):
    """Add item to cart"""
    variant_id: str = Field(..., description="Product variant ID")
    fulfillment_location_id: str = Field(..., description="Store or warehouse ID")
    quantity: int = Field(1, ge=1, description="Quantity to add")


class CartItemUpdate(BaseModel):
    """Update cart item quantity"""
    quantity: int = Field(..., gt=0, description="New quantity for the cart item")


class CheckoutRequest(BaseModel):
    """Checkout request"""
    order_type: str = Field(..., description="'delivery' or 'pickup'")
    pickup_fulfillment_location_id: Optional[str] = None
    address_id: Optional[str] = None
    promotion_code: Optional[str] = None


class ReturnRequest(BaseModel):
    """Initiate return"""
    order_id: str
    order_item_id: str
    reason: str
    type: str = "refund"  # 'refund' or 'exchange'


class CartResponse(BaseModel):
    """Cart with items"""
    id: str
    user_id: Optional[str] = None
    status: str
    items: List[Dict[str, Any]]
    total: float
    item_count: int
    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    """Order with items"""
    id: str
    user_id: Optional[str] = None
    status: str
    total_amount: float
    currency: str
    items: List[Dict[str, Any]]
    created_at: datetime


# ============================================================================
# INVENTORY SCHEMAS
# ============================================================================

class StockUpdateRequest(BaseModel):
    """Stock update"""
    store_id: str
    variant_id: str
    delta_quantity: int


class InventoryFullUpdate(BaseModel):
    """Full inventory update"""
    variant_id: str
    store_id: str
    quantity_on_hand: Optional[int] = None
    section_id: Optional[str] = None
    aisle_number: Optional[int] = None
    bay_number: Optional[int] = None
    shelf_height: Optional[int] = None
    display_location: Optional[str] = None


class InventoryAdjustRequest(BaseModel):
    """Inventory adjustment"""
    variant_id: str
    quantity_change: int
    reason: Optional[str] = None


class StockUpdate(BaseModel):
    """Inward stock update"""
    product_variant_id: str
    quantity: int
    aisle: Optional[int] = None
    shelf: Optional[int] = None
    bay: Optional[int] = None
    section_id: Optional[str] = None
    reason: Optional[str] = "Inward Stock"


class StockAdjustment(BaseModel):
    """Stock adjustment"""
    warehouse_id: str
    variant_id: str
    quantity_change: int
    reason: str


# ============================================================================
# CATALOG MANAGEMENT SCHEMAS
# ============================================================================

class ProductCreate(BaseModel):
    """Create product"""
    name: str
    description: str
    base_price: float = Field(..., ge=0)
    category_id: str
    gender: str  # 'men', 'women', 'kids', 'unisex'
    season: str = "all_season"
    usage_type: str = "casual"
    style_tags: List[str] = []


class VariantCreate(BaseModel):
    """Create product variant"""
    product_id: str
    sku: str
    color_name: str
    size_label: str
    color_hex: Optional[str] = "#000000"
    material: Optional[str] = None
    price_override: Optional[float] = None
    attributes: Optional[dict] = {}
    fit_type: Optional[str] = None
    image_url: Optional[str] = None


class CategoryCreate(BaseModel):
    """Create category"""
    name: str
    slug: str
    parent_id: Optional[str] = None


# ============================================================================
# LOCATION MANAGEMENT SCHEMAS
# ============================================================================

class StoreCreate(BaseModel):
    """Create store"""
    store_code: str
    name: str
    type: str = "store"  # 'store', 'warehouse', 'dark_store'
    address_line_1: str
    city: str
    latitude: float
    longitude: float


class LocationCreate(BaseModel):
    """Create fulfillment location"""
    name: str
    type: str  # 'store' or 'warehouse'
    city: str
    address_line_1: str
    latitude: float
    longitude: float
    store_code: Optional[str] = None
    warehouse_code: Optional[str] = None


# ============================================================================
# SUPPORT SCHEMAS
# ============================================================================

class TicketCreate(BaseModel):
    """Create support ticket - user_id comes from auth"""
    issue_summary: str = Field(..., description="Brief issue description")
    conversation_summary: Optional[str] = Field(None, description="Full conversation context")
    sentiment_score: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    order_id: Optional[str] = None
    ticket_type: Optional[str] = Field("general", description="order_issue, payment_issue, inventory_issue, delivery_issue, general")
    priority: Optional[str] = Field("medium", description="low, medium, high, urgent")
    """Create support ticket"""
    user_id: str
    order_id: Optional[str] = None
    issue_summary: str
    conversation_summary: str
    sentiment_score: float


class TicketUpdate(BaseModel):
    """Update ticket status"""
    status: str
    notes: Optional[str] = None


# ============================================================================
# RBAC SCHEMAS
# ============================================================================

class RoleAssignRequest(BaseModel):
    """Assign role to user"""
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None


class RoleRevoke(BaseModel):
    """Revoke role from user"""
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None


# ============================================================================
# PROMOTION SCHEMAS
# ============================================================================

class PromotionCreate(BaseModel):
    """Create promotion"""
    code: str
    name: str
    discount_type: str  # 'percentage', 'fixed_amount', 'bogo'
    discount_value: float
    constraints: Dict = {}
    max_usage_global: int


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class FootprintCreate(BaseModel):
    """Track user behavior"""
    event_type: str
    event_data: Dict[str, Any]
    session_id: Optional[str] = None


# ============================================================================
# CHANNEL SCHEMAS
# ============================================================================

class ChannelMessage(BaseModel):
    """Channel message"""
    channel_type: str  # 'web', 'kiosk', 'whatsapp'
    channel_id: str
    message: str
    locale: Optional[str] = "en"


# ============================================================================
# FEEDBACK SCHEMAS
# ============================================================================

class ReviewCreate(BaseModel):
    """Create product review"""
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    review_text: str


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationCreate(BaseModel):
    """Create notification"""
    user_id: str
    title: str
    body: str
    type: Optional[str] = "info"


# ============================================================================
# PROFILE SCHEMAS
# ============================================================================

class AddressCreate(BaseModel):
    """Create user address"""
    type: str = "home"
    address_line: str
    city: str
    pincode: str
    is_default: bool = False


class StyleProfileUpdate(BaseModel):
    """Update style profile"""
    preferred_colors: List[str]
    preferred_fits: List[str]
    preferred_tags: Dict[str, str]


# ============================================================================
# ORDER MANAGEMENT SCHEMAS
# ============================================================================

class OrderStatusUpdate(BaseModel):
    """Update order status"""
    status: str


# ============================================================================
# UI-FRIENDLY RESPONSE WRAPPERS
# ============================================================================

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

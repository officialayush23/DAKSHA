from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date

class AddressCreate(BaseModel):
    type: str 
    address_line: str
    city: str
    pincode: str

class UserRegistration(BaseModel):
    full_name: str
    gender: str
    date_of_birth: date
    preferred_languages: List[str] = ["en"]
    address: AddressCreate

class LoginWithPhoneRequest(BaseModel):
    phone_number: str
    guest_id: str

class AddToCartRequest(BaseModel):
    variant_id: str
    store_id: str
    quantity: int

class ReturnRequest(BaseModel):
    order_item_id: str
    order_id: str
    type: str
    reason: str

class CheckoutRequest(BaseModel):
    order_type: str
    store_id: str
    address_id: str
    promotion_code: Optional[str] = None

class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    review_text: str

class ProductCreate(BaseModel):
    name: str
    description: str
    style_tags: List[str]

class VariantCreate(BaseModel):
    product_id: str
    size: str
    color: str
    sku: str
    price: float
    stock_quantity: int

class StoreCreate(BaseModel):
    name: str
    address: str
    city: str

class InventoryFullUpdate(BaseModel):
    variant_id: str
    store_id: str
    stock_count: Optional[int] = None
    aisle: Optional[str] = None
    shelf: Optional[str] = None

class PromotionCreate(BaseModel):
    code: str
    name: str
    discount_type: str
    discount_value: float
    constraints: Dict
    max_usage_global: int

class FootprintCreate(BaseModel):
    user_id: str
    event_type: str
    page_url: str
    details: Dict

class ChannelMessage(BaseModel):
    channel_type: str
    channel_id: str
    message: str

class StyleProfileUpdate(BaseModel):
    preferred_colors: List[str]
    preferred_brands: List[str]
    style_tags: List[str]

class TicketCreate(BaseModel):
    user_id: str
    issue_summary: str
    conversation_summary: str
    sentiment_score: float
    order_id: Optional[str] = None

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None

class PaymentMethodCreate(BaseModel):
    gateway_token_id: str
    card_last4: str
    card_brand: str

class UserRegisterRequest(BaseModel):
    full_name: str
    phone_number: str
    gender: str
    date_of_birth: date
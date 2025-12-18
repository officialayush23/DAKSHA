from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import time

# --- Catalog Management ---

class ProductCreate(BaseModel):
    name: str
    description: str
    base_price: float
    category_id: str
    gender: str  # 'men', 'women', 'kids', 'unisex' (product.gender_enum)
    season: str = "all_season"
    usage_type: str = "casual"  # 'casual', 'formal', etc.
    style_tags: List[str] = []


class VariantCreate(BaseModel):
    product_id: str
    sku: str
    color_name: str
    size_label: str
    color_hex: Optional[str] = "#000000"
    # --- NEW FIELDS MATCHING DB ---
    material: Optional[str] = None
    price_override: Optional[float] = None
    attributes: Optional[dict] = {} 
    fit_type: Optional[str] = None
    image_url: Optional[str] = None


# --- Store Management ---
class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: Optional[str] = None

class StoreCreate(BaseModel):
    store_code: str
    name: str
    type: str = "store"  # store | warehouse | dark_store
    address_line_1: str
    city: str
    latitude: float
    longitude: float

class StockAdjustment(BaseModel):
    warehouse_id: str
    variant_id: str
    quantity_change: int # Can be negative (shrinkage) or positive (restock)
    reason: str
class StockUpdate(BaseModel):
    """
    Used for Inward Stock (adding new inventory).
    """
    product_variant_id: str
    quantity: int
    aisle: Optional[int] = None
    shelf: Optional[int] = None
    bay: Optional[int] = None      # ✅ Added matching schema
    section_id: Optional[str] = None # ✅ Added matching schema
    reason: Optional[str] = "Inward Stock"

class InventoryAdjustRequest(BaseModel):
    variant_id: str
    quantity_change: int 
    reason: Optional[str] = None

class InventoryFullUpdate(BaseModel):
    variant_id: str
    store_id: str
    quantity_on_hand: Optional[int] = None
    section_id: Optional[str] = None
    aisle_number: Optional[int] = None
    bay_number: Optional[int] = None
    shelf_height: Optional[int] = None
    display_location: Optional[str] = None
class PromotionCreate(BaseModel):
    code: str
    name: str
    discount_type: str  # 'percentage' | 'fixed_amount' | 'bogo'
    discount_value: float
    constraints: Dict = {}
    max_usage_global: int


class OrderStatusUpdate(BaseModel):
    status: str
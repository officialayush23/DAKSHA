# app/models/management.py
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
    usage_type: str  # 'casual', 'formal', etc.
    style_tags: List[str]


class VariantCreate(BaseModel):
    product_id: str
    sku: str
    color_name: str
    size_label: str
    material: str
    price_override: Optional[float] = None
    attributes: Dict = {}


# --- Store Management ---


class StoreCreate(BaseModel):
    store_code: str
    name: str
    type: str = "store"  # store | warehouse | dark_store
    address_line_1: str
    city: str
    latitude: float
    longitude: float


class InventoryFullUpdate(BaseModel):
    """
    Used by Store Managers to move items or correct counts.

    This maps directly to the inventory table:
      - store_id
      - product_variant_id
      - quantity_on_hand / reserved
      - location fields (aisle / bay / shelf / display_location / section_id)
    """

    variant_id: str
    store_id: str

    quantity_on_hand: Optional[int] = None
    section_id: Optional[str] = None
    aisle_number: Optional[int] = None
    bay_number: Optional[int] = None
    shelf_height: Optional[int] = None
    display_location: Optional[str] = None  # e.g. "Rack 4"


# --- Promotion Management ---


class PromotionCreate(BaseModel):
    code: str
    name: str
    discount_type: str  # 'percentage' | 'fixed_amount' | 'bogo'
    discount_value: float
    constraints: Dict = {}
    max_usage_global: int

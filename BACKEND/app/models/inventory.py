# app/models/inventory.py

from pydantic import BaseModel
from typing import Optional


class StockUpdateRequest(BaseModel):
    store_id: str
    variant_id: str
    delta_quantity: int


class InventoryFullUpdate(BaseModel):
    variant_id: str
    store_id: str
    quantity_on_hand: Optional[int] = None
    section_id: Optional[str] = None
    aisle_number: Optional[int] = None
    bay_number: Optional[int] = None
    shelf_height: Optional[int] = None
    display_location: Optional[str] = None

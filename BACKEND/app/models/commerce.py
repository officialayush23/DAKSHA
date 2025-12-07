from pydantic import BaseModel
from typing import Optional


class AddToCartRequest(BaseModel):
    variant_id: str
    store_id: str
    quantity: int = 1


class ReturnRequest(BaseModel):
    order_id: str
    order_item_id: str
    reason: str
    type: str = "refund"  # or 'exchange'


class CheckoutRequest(BaseModel):
    order_type: str  # 'delivery' | 'pickup' | 'reservation'
    store_id: Optional[str] = None
    address_id: Optional[str] = None
    promotion_code: Optional[str] = None

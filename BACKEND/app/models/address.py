from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class AddressResponse(BaseModel):
    id: UUID
    type: Optional[str] = "home"
    address_line: str
    city: str
    pincode: str
    is_default: bool

    class Config:
        from_attributes = True

class PaymentMethodResponse(BaseModel):
    id: UUID
    provider: str
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    is_default: bool

    class Config:
        from_attributes = True
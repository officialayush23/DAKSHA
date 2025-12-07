from pydantic import BaseModel
from typing import List, Dict


class AddressCreate(BaseModel):
    type: str = "home"
    address_line: str
    city: str
    pincode: str
    is_default: bool = False


class StyleProfileUpdate(BaseModel):
    preferred_colors: List[str]
    preferred_fits: List[str]
    preferred_tags: Dict[str, str]

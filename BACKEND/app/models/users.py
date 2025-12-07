# app/models/users.py
from typing import Optional
from datetime import date
from pydantic import BaseModel

class UserProfileUpdate(BaseModel):
    """
    Used for both /users/me PATCH and /users/register.
    All fields optional so partial updates & registration both work.
    """
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None  # plain varchar, NOT gender_enum
    date_of_birth: Optional[date] = None  # accepts "YYYY-MM-DD" string

class PaymentMethodCreate(BaseModel):
    gateway_token_id: str
    card_last4: str
    card_brand: str

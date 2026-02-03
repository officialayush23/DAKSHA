# app/graphs/checkout_state.py
from typing import TypedDict, Optional
from uuid import UUID
from app.enums.db_enums import CheckoutStateEnum

class CheckoutGraphState(TypedDict):
    checkout_id: UUID
    user_id: UUID
    cart_id: UUID

    state: CheckoutStateEnum

    locked_price: Optional[float]
    payment_attempts: int
    last_error: Optional[str]

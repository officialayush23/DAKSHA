# app/agents/guards.py
from app.enums.db_enums import CheckoutStateEnum

BLOCKING_STATES = {
    CheckoutStateEnum.ROLLED_BACK,
}

PAYMENT_ALLOWED = {
    CheckoutStateEnum.PRICE_LOCKED,
    CheckoutStateEnum.COUPON_APPLIED,
    CheckoutStateEnum.PAYMENT_FAILED,
}

def can_retry_payment(state: CheckoutStateEnum) -> bool:
    return state in PAYMENT_ALLOWED

def can_resume_checkout(state: CheckoutStateEnum) -> bool:
    return state not in BLOCKING_STATES

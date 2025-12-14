# app/routers/payments.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/intent/{order_id}")
async def create_intent(order_id: str, user_id: str = Depends(get_current_user_id)):
    return PaymentService.create_payment_intent(order_id, user_id)


@router.post("/confirm/{payment_id}")
async def confirm_payment(
    payment_id: str,
    success: bool = True,
    user_id: str = Depends(get_current_user_id),
):
    return await PaymentService.confirm_payment(payment_id, success)


@router.post("/capture")
async def capture_payment(order_id: str, provider: str, ref: str, amount: float):
    return PaymentService.capture_payment(order_id, provider, ref, amount)

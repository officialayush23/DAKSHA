from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import get_current_user_id
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])

class PaymentFailureReport(BaseModel):
    order_id: str
    reason: str

@router.post("/intent/{order_id}")
async def create_intent(order_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Step 1 of Payment: Signal intent.
    AI Agent uses this to detect 'Abandonment' if it never succeeds.
    """
    return PaymentService.create_payment_intent(order_id, user_id)

@router.post("/failure")
async def report_failure(payload: PaymentFailureReport, user_id: str = Depends(get_current_user_id)):
    """
    Frontend calls this if Razorpay/Stripe returns an error.
    AI Agent reads this to ask: "I saw your payment failed due to [reason]. Need help?"
    """
    PaymentService.record_failure(payload.order_id, payload.reason)
    return {"status": "recorded"}

@router.post("/capture")
async def capture_payment_manual(order_id: str, provider: str, ref: str, amount: float):
    """
    Server-side webhook handler (or manual capture).
    """
    return PaymentService.capture_payment(order_id, provider, ref, amount)
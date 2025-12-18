from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.payment_service import PaymentService
from app.database import supabase
import uuid

router = APIRouter(prefix="/dummy-payment", tags=["Dummy Payment Gateway"])

class DummyPaymentRequest(BaseModel):
    order_id: str
    amount: float
    success: bool = True # Toggle this from Frontend

@router.post("/process")
async def process_dummy_payment(payload: DummyPaymentRequest):
    """
    Simulates a payment gateway callback.
    """
    # 1. Fetch Order to verify existence
    order = supabase.table("orders").select("id, total_amount, status").eq("id", payload.order_id).maybe_single().execute()
    
    if not order.data:
        raise HTTPException(404, "Order not found")
    
    if order.data['status'] != 'pending':
        return {"status": "ignored", "message": f"Order is already {order.data['status']}"}

    # 2. Simulate Provider Logic
    provider_ref = f"dum_{uuid.uuid4().hex[:12]}"
    
    if payload.success:
        # ✅ Call the real service to capture and upgrade loyalty
        try:
            result = PaymentService.capture_payment(
                order_id=payload.order_id,
                provider="dummy_gateway",
                provider_ref=provider_ref,
                amount=payload.amount
            )
            return {"status": "success", "transaction_id": provider_ref, "data": result}
        except Exception as e:
            raise HTTPException(500, f"Payment Capture Failed: {str(e)}")
            
    else:
        # ❌ Log failure in payment_attempts
        supabase.table("payment_attempts").insert({
            "payment_id": None, # No payment record created yet
            "gateway_transaction_id": provider_ref,
            "status": "failed",
            "error_message": "User simulated a failure",
            "gateway_response_json": {"reason": "dummy_decline"}
        }).execute()
        
        return {"status": "failed", "message": "Payment declined by dummy gateway"}
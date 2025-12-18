from datetime import datetime
from fastapi import HTTPException
from app.database import supabase
from app.services.human_handoff_service import HumanHandoffService
import logging
import uuid

logger = logging.getLogger("payment_service")

class PaymentService:

    @staticmethod
    def create_payment_intent(order_id: str, user_id: str):
        # 1. Fetch Order
        order = supabase.table("orders").select("total_amount, status").eq("id", order_id).single().execute().data
        if not order: raise HTTPException(404, "Order not found")
        
        # 2. Check existing intent
        existing = supabase.table("payments").select("id, provider_reference").eq("order_id", order_id).eq("status", "initiated").maybe_single().execute()
        if existing.data:
            return {"payment_id": existing.data['id'], "client_secret": existing.data['provider_reference']}

        # 3. Create Intent
        gateway_id = f"pi_{uuid.uuid4().hex[:16]}"
        payment = supabase.table("payments").insert({
            "order_id": order_id,
            "user_id": user_id,
            "amount": order['total_amount'],
            "currency": "INR",
            "provider": "razorpay_sim",
            "provider_reference": gateway_id,
            "status": "initiated",
            "created_at": datetime.utcnow().isoformat()
        }).execute().data[0]

        return {"payment_id": payment['id'], "client_secret": gateway_id}

    @staticmethod
    def capture_payment(order_id: str, provider: str, provider_ref: str, amount: float):
        # 1. Validate Order
        order = supabase.table("orders").select("*").eq("id", order_id).single().execute().data
        if not order: raise HTTPException(404, "Order not found")
        if order["status"] in ["paid", "shipped", "delivered"]: return {"status": "already_paid"}

        # 2. Update Payment Record
        intent = supabase.table("payments").select("id").eq("order_id", order_id).eq("status", "initiated").maybe_single().execute()
        
        if intent.data:
            payment = supabase.table("payments").update({
                "status": "captured",
                "captured_at": datetime.utcnow().isoformat(),
                "provider_reference": provider_ref
            }).eq("id", intent.data['id']).execute().data[0]
        else:
            payment = supabase.table("payments").insert({
                "order_id": order_id,
                "amount": amount,
                "user_id": order['user_id'],
                "provider": provider,
                "provider_reference": provider_ref,
                "status": "captured",
                "captured_at": datetime.utcnow().isoformat()
            }).execute().data[0]

        # 3. Escrow & Loyalty (Safe Mode)
        try:
            PaymentService._credit_escrow(order_id, amount)
            PaymentService._upgrade_loyalty(order['user_id'], amount)
        except Exception as e:
            logger.error(f"Post-payment hook failed: {e}")

        # 4. Finalize Order
        supabase.table("orders").update({"status": "paid"}).eq("id", order_id).execute()
        return payment

    @staticmethod
    def record_failure(order_id: str, reason: str):
        supabase.table("payment_attempts").insert({
            "gateway_transaction_id": f"fail_{uuid.uuid4().hex[:8]}",
            "status": "failed",
            "error_message": reason,
            "gateway_response_json": {"order_id": order_id},
            "attempted_at": datetime.utcnow().isoformat()
        }).execute()

    @staticmethod
    def _credit_escrow(order_id: str, amount: float):
        wallet = supabase.table("wallets").select("id").eq("type", "escrow").maybe_single().execute().data
        if wallet:
            supabase.table("wallet_transactions").insert({
                "wallet_id": wallet["id"],
                "amount": amount,
                "type": "credit",
                "status": "locked",
                "reference_type": "order",
                "reference_id": order_id
            }).execute()

    @staticmethod
    def _upgrade_loyalty(user_id: str, amount: float):
        points_row = supabase.table("users").select("loyalty_points").eq("id", user_id).single().execute().data
        if points_row:
            new_pts = (points_row.get("loyalty_points") or 0) + int(amount / 10)
            tier = "bronze"
            if new_pts > 5000: tier = "gold"
            elif new_pts > 1000: tier = "silver"
            supabase.table("users").update({"loyalty_points": new_pts, "loyalty_tier": tier}).eq("id", user_id).execute()
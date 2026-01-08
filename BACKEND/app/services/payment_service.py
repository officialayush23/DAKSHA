# app/services/payment_service.py
from datetime import datetime
from fastapi import HTTPException
from app.core.database import supabase_admin
from app.services.human_handoff_service import HumanHandoffService
import logging
import uuid

logger = logging.getLogger("payment_service")

class PaymentService:

    @staticmethod
    def create_payment_intent(order_id: str, user_id: str):
        # 1. Fetch Order
        order = supabase_admin.table("orders").select("total_amount, status").eq("id", order_id).single().execute().data
        if not order: raise HTTPException(404, "Order not found")
        
        # 2. Check existing intent
        existing = supabase_admin.table("payments").select("id, idempotency_key").eq("order_id", order_id).eq("status", "initiated").maybe_single().execute()
        if existing.data:
            return {"payment_id": existing.data['id'], "client_secret": existing.data.get('idempotency_key', '')}

        # 3. Get payment provider ID
        provider = supabase_admin.table("payment_providers").select("id").eq("name", "razorpay_sim").maybe_single().execute().data
        if not provider:
            raise HTTPException(500, "Payment provider not configured")
        
        # 4. Create Intent
        gateway_id = f"pi_{uuid.uuid4().hex[:16]}"
        # In Supabase v2, insert() already returns data - no need for .select()
        payment = supabase_admin.table("payments").insert({
            "order_id": order_id,
            "provider_id": provider['id'],
            "status": "initiated",
            "amount": order['total_amount'],
            "currency": "INR",
            "idempotency_key": f"{order_id}_{gateway_id}",
        }).execute().data[0]

        return {"payment_id": payment['id'], "client_secret": gateway_id}

    @staticmethod
    def capture_payment(order_id: str, provider: str, provider_ref: str, amount: float):
        # 1. Validate Order
        order = supabase_admin.table("orders").select("*").eq("id", order_id).single().execute().data
        if not order: raise HTTPException(404, "Order not found")
        if order["status"] in ["paid", "shipped", "delivered"]: return {"status": "already_paid"}

        # 2. Get or create payment record
        intent = supabase_admin.table("payments").select("id, status").eq("order_id", order_id).eq("status", "initiated").maybe_single().execute()
        
        if intent.data:
            payment_id = intent.data['id']
            # Update provider_reference if needed (non-transactional field)
            supabase_admin.table("payments").update({
                "provider_reference": provider_ref
            }).eq("id", payment_id).execute()
        else:
            # Get payment provider ID
            provider_row = supabase_admin.table("payment_providers").select("id").eq("name", provider).maybe_single().execute().data
            if not provider_row:
                raise HTTPException(500, f"Payment provider '{provider}' not found")
            
            # Create payment record (no RPC for payment creation, only for capture)
            # In Supabase v2, insert() already returns data - no need for .select()
            payment = supabase_admin.table("payments").insert({
                "order_id": order_id,
                "provider_id": provider_row['id'],
                "status": "authorized",  # RPC expects 'authorized' status
                "amount": amount,
                "currency": "INR",
                "idempotency_key": f"{order_id}_{provider_ref}",
            }).execute().data[0]
            payment_id = payment['id']

        # 3. Capture payment to escrow using RPC (updates payment status to 'captured' and creates ledger entry)
        from app.core.rpc import RPCService
        
        # Get escrow wallet ID
        escrow_wallet = supabase_admin.table("wallets").select("id").eq("wallet_type", "escrow").maybe_single().execute().data
        if not escrow_wallet:
            logger.error("Escrow wallet not found")
            raise HTTPException(500, "Escrow wallet not configured")
        
        # Use RPC to capture payment to escrow (handles ledger entries atomically and updates payment status)
        RPCService.capture_payment_to_escrow(
            payment_id=payment_id,
            escrow_wallet_id=escrow_wallet['id'],
        )
        
        # Read back payment to return
        payment = supabase_admin.table("payments").select("*").eq("id", payment_id).single().execute().data
        
        # 4. Assert order is paid (verifies escrow balance)
        RPCService.assert_order_paid(
            order_id=order_id,
            escrow_wallet_id=escrow_wallet['id'],
        )
        
        # 5. Finalize Order - Use RPC for state transition
        RPCService.transition_order_state(
            order_id=order_id,
            from_state="pending_payment",
            to_state="paid",
        )
        
        # 6. Commit inventory for order (when paid)
        RPCService.commit_inventory_for_order(order_id)
        
        # 7. Loyalty points (non-transactional, safe to do after)
        try:
            PaymentService._upgrade_loyalty(order['user_id'], amount)
        except Exception as e:
            logger.error(f"Loyalty upgrade failed: {e}")
        
        return payment

    @staticmethod
    def record_failure(order_id: str, reason: str):
        supabase_admin.table("payment_attempts").insert({
            "gateway_transaction_id": f"fail_{uuid.uuid4().hex[:8]}",
            "status": "failed",
            "error_message": reason,
            "gateway_response_json": {"order_id": order_id},
            "attempted_at": datetime.utcnow().isoformat()
        }).execute()

    @staticmethod
    def _credit_escrow(order_id: str, amount: float):
        wallet = supabase_admin.table("wallets").select("id").eq("type", "escrow").maybe_single().execute().data
        if wallet:
            supabase_admin.table("wallet_transactions").insert({
                "wallet_id": wallet["id"],
                "amount": amount,
                "type": "credit",
                "status": "locked",
                "reference_type": "order",
                "reference_id": order_id
            }).select("*").execute()

    @staticmethod
    def _upgrade_loyalty(user_id: str, amount: float):
        points_row = supabase_admin.table("users").select("loyalty_points").eq("id", user_id).single().execute().data
        if points_row:
            new_pts = (points_row.get("loyalty_points") or 0) + int(amount / 10)
            tier = "bronze"
            if new_pts > 5000: tier = "gold"
            elif new_pts > 1000: tier = "silver"
            supabase_admin.table("users").update({"loyalty_points": new_pts, "loyalty_tier": tier}).eq("id", user_id).execute()
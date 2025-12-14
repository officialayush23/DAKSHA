# app/services/payment_service.py
from datetime import datetime
from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus
from app.services.human_handoff_service import HumanHandoffService


class PaymentService:

    # ---------------------------------------------------------
    # 1️⃣ AUTHORIZE + CAPTURE PAYMENT
    # ---------------------------------------------------------
    @staticmethod
    def capture_payment(order_id: str, provider: str, provider_ref: str, amount: float):
        order = (
            supabase.table("orders")
            .select("*")
            .eq("id", order_id)
            .single()
            .execute()
        ).data

        if not order:
            raise HTTPException(404, "Order not found")

        if order["status"] != "pending":
            raise HTTPException(409, "Order already paid or cancelled")

        payment = (
            supabase.table("payments")
            .insert({
                "order_id": order_id,
                "amount": amount,
                "currency": "INR",
                "provider": provider,
                "provider_reference": provider_ref,
                "status": "captured",
                "captured_at": datetime.utcnow(),
            })
            .execute()
        ).data[0]

        # Escrow credit (LOCKED)
        PaymentService._credit_escrow(order_id, amount)

        # Move order forward
        supabase.table("orders") \
            .update({"status": "paid"}) \
            .eq("id", order_id) \
            .execute()

        return payment

    # ---------------------------------------------------------
    # 2️⃣ CREDIT ESCROW WALLET
    # ---------------------------------------------------------
    @staticmethod
    def _credit_escrow(order_id: str, amount: float):
        wallet = (
            supabase.table("wallets")
            .select("*")
            .eq("type", "escrow")
            .single()
            .execute()
        ).data

        if not wallet:
            raise HTTPException(500, "Escrow wallet missing")

        supabase.table("wallet_transactions").insert({
            "wallet_id": wallet["id"],
            "amount": amount,
            "type": "credit",
            "status": "locked",
            "reference_type": "order",
            "reference_id": order_id,
            "created_at": datetime.utcnow(),
        }).execute()

    # ---------------------------------------------------------
    # 3️⃣ RELEASE PAYOUT AFTER DELIVERY
    # ---------------------------------------------------------
    @staticmethod
    def release_payout(order_id: str):
        fulfillment = (
            supabase.table("fulfillments")
            .select("*")
            .eq("order_id", order_id)
            .maybe_single()
            .execute()
        ).data

        if not fulfillment or fulfillment["status"] != "delivered":
            raise HTTPException(409, "Order not delivered")

        tx = (
            supabase.table("wallet_transactions")
            .select("*")
            .eq("reference_id", order_id)
            .eq("status", "locked")
            .maybe_single()
            .execute()
        ).data

        if not tx:
            raise HTTPException(409, "No escrow transaction found")

        # Unlock escrow
        supabase.table("wallet_transactions") \
            .update({"status": "released"}) \
            .eq("id", tx["id"]) \
            .execute()

        # Schedule payout
        payout = (
            supabase.table("payouts")
            .insert({
                "order_id": order_id,
                "amount": tx["amount"],
                "status": "scheduled",
                "scheduled_at": datetime.utcnow(),
            })
            .execute()
        ).data[0]

        return payout

    # ---------------------------------------------------------
    # 4️⃣ REFUND (FAILURE / CANCELLATION)
    # ---------------------------------------------------------
    @staticmethod
    def refund(order_id: str, reason: str):
        tx = (
            supabase.table("wallet_transactions")
            .select("*")
            .eq("reference_id", order_id)
            .eq("status", "locked")
            .maybe_single()
            .execute()
        ).data

        if not tx:
            raise HTTPException(409, "No refundable escrow")

        supabase.table("wallet_transactions").update({
            "status": "reversed",
            "metadata": {"reason": reason},
        }).eq("id", tx["id"]).execute()

        supabase.table("orders").update({
            "status": "refunded"
        }).eq("id", order_id).execute()

        HumanHandoffService.trigger(
            session_id=None,
            user_id=None,
            reason="payment_refund",
            summary=reason,
        )

        return {"status": "refunded"}

# app/services/payment_service.py

from fastapi import HTTPException
from app.database import supabase
from datetime import datetime
import uuid


class PaymentService:

    # ---------------------------------------------------------
    # CREATE PAYMENT INTENT
    # ---------------------------------------------------------
    @staticmethod
    def create_payment_intent(order_id: str, user_id: str):
        """
        Creates a payment intent entry in DB.
        External gateways (Razorpay/Stripe) will use this ID.
        """

        # Validate order ownership
        order = (
            supabase.table("orders")
            .select("id, user_id, total_amount, discount_amount, status")
            .eq("id", order_id)
            .single()
            .execute()
        ).data

        if not order:
            raise HTTPException(404, "Order not found")

        if order["user_id"] != user_id:
            raise HTTPException(403, "Not your order")

        if order["status"] not in ("pending", "processing"):
            raise HTTPException(400, "Order is not payable")

        final_amount = float(order["total_amount"]) - float(order["discount_amount"] or 0)

        # Create internal payment record
        payment = (
            supabase.table("payments")
            .insert(
                {
                    "order_id": order_id,
                    "user_id": user_id,
                    "provider": "razorpay",
                    "status": "initiated",
                    "amount": final_amount,
                }
            )
            .execute()
        ).data[0]

        return {
            "payment_id": payment["id"],
            "amount": final_amount,
            "currency": "INR",
        }

    # ---------------------------------------------------------
    # CONFIRM PAYMENT (GATEWAY CALLBACK)
    # ---------------------------------------------------------
    @staticmethod
    async def confirm_payment(payment_id: str, success: bool):
        """
        Finalizes payment + updates order:
        - success → status = paid
        - failure → status = failed
        """

        pay = (
            supabase.table("payments")
            .select("*, orders(id, status)")
            .eq("id", payment_id)
            .single()
            .execute()
        ).data

        if not pay:
            raise HTTPException(404, "Payment not found")

        order_id = pay["order_id"]
        new_status = "success" if success else "failed"

        # Update payment record
        supabase.table("payments").update({"status": new_status}).eq("id", payment_id).execute()

        # Record attempt
        supabase.table("payment_attempts").insert(
            {
                "payment_id": payment_id,
                "status": new_status,
                "attempted_at": datetime.utcnow().isoformat(),
            }
        ).execute()

        # Update order
        supabase.table("orders").update(
            {"status": "paid" if success else "cancelled"}
        ).eq("id", order_id).execute()

        return {
            "status": "completed" if success else "failed",
            "order_id": order_id,
        }

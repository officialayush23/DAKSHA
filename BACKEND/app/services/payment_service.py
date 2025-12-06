from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus


class PaymentService:
    @staticmethod
    def create_payment_intent(order_id: str, user_id: str) -> dict:
        order = (
            supabase.table("orders")
            .select("*")
            .eq("id", order_id)
            .single()
            .execute()
        )
        if not order.data or order.data["user_id"] != user_id:
            raise HTTPException(404, "Order not found")

        amount = float(order.data["total_amount"] - order.data["discount_amount"])

        res = (
            supabase.table("payments")
            .insert(
                {
                    "order_id": order_id,
                    "user_id": user_id,
                    "provider": "mock_gateway",
                    "status": "initiated",
                    "amount": amount,
                }
            )
            .execute()
        )
        payment = res.data[0]
        payment["payment_url"] = f"https://mock-gateway.test/pay/{payment['id']}"
        return payment

    @staticmethod
    async def confirm_payment(
        payment_id: str, success: bool, error_message: str | None = None
    ):
        payment_res = (
            supabase.table("payments")
            .select("*")
            .eq("id", payment_id)
            .single()
            .execute()
        )
        if not payment_res.data:
            raise HTTPException(404, "Payment not found")

        payment = payment_res.data

        attempt = {
            "payment_id": payment_id,
            "gateway_transaction_id": f"mock_tx_{payment_id}",
            "status": "success" if success else "failed",
            "error_code": None if success else "ERR_PAYMENT",
            "error_message": None if success else (error_message or "Payment failed"),
        }
        supabase.table("payment_attempts").insert(attempt).execute()

        new_status = "success" if success else "failed"
        supabase.table("payments").update({"status": new_status}).eq(
            "id", payment_id
        ).execute()

        order_status = "paid" if success else "pending"
        order_res = (
            supabase.table("orders")
            .update({"status": order_status})
            .eq("id", payment["order_id"])
            .execute()
        )
        order = order_res.data[0]

        await EventBus.notify_user(
            order["user_id"],
            "order_status_updated",
            {"order_id": order["id"], "status": order_status},
        )

        return {"order": order, "payment_status": new_status}

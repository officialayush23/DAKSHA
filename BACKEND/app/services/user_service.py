from fastapi import HTTPException
from app.database import supabase


class UserService:
    @staticmethod
    async def ensure_user_exists(user_id: str) -> dict:
        res = supabase.table("users").select("*").eq("id", user_id).single().execute()
        if res.data:
            return res.data

        new_profile = {
            "id": user_id,
            "is_active": True,
        }
        created = supabase.table("users").insert(new_profile).execute()
        if not created.data:
            raise HTTPException(500, "Failed to create user profile")
        return created.data[0]

    @staticmethod
    async def update_profile(user_id: str, data: dict) -> dict:
        if "phone_number" in data and data["phone_number"]:
            check = (
                supabase.table("users")
                .select("id")
                .eq("phone_number", data["phone_number"])
                .neq("id", user_id)
                .execute()
            )
            if check.data:
                raise HTTPException(400, "Phone number already in use")

        res = supabase.table("users").update(data).eq("id", user_id).execute()
        if not res.data:
            raise HTTPException(404, "User not found")
        return res.data[0]

    @staticmethod
    async def add_payment_method(user_id: str, token_id: str, last4: str, brand: str):
        supabase.table("user_payment_methods").update(
            {"is_default": False}
        ).eq("user_id", user_id).execute()

        res = supabase.table("user_payment_methods").insert(
            {
                "user_id": user_id,
                "provider": "razorpay",
                "gateway_token_id": token_id,
                "card_last4": last4,
                "card_brand": brand,
                "is_default": True,
            }
        ).execute()

        if not res.data:
            raise HTTPException(500, "Failed to save payment method")
        return res.data[0]

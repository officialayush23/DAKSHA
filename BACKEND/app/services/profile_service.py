# app/services/profile_service.py

from app.database import supabase


class ProfileService:
    @staticmethod
    def get_profile(user_id: str) -> dict:
        user = (
            supabase.table("users")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )

        style = (
            supabase.table("user_style_profile")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "user": user.data,
            "style": style.data[0] if style.data else {},
        }

    @staticmethod
    def add_address(user_id: str, addr: dict) -> dict:
        if addr.get("is_default"):
            supabase.table("user_addresses").update(
                {"is_default": False}
            ).eq("user_id", user_id).execute()

        res = (
            supabase.table("user_addresses")
            .insert({**addr, "user_id": user_id})
            .execute()
        )
        return res.data[0]

    @staticmethod
    def update_style(user_id: str, profile: dict):
        res = (
            supabase.table("user_style_profile")
            .upsert(
                {
                    "user_id": user_id,
                    "preferred_colors": profile["preferred_colors"],
                    "preferred_fits": profile["preferred_fits"],
                    "preferred_tags": profile["preferred_tags"],
                }
            )
            .execute()
        )
        return res.data[0] if res.data else {}

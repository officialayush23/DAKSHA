from app.database import supabase


class LoyaltyService:
    @staticmethod
    def get_loyalty_summary(user_id: str):
        user = (
            supabase.table("users")
            .select("loyalty_points, loyalty_tier")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not user.data:
            return None

        points = user.data["loyalty_points"]

        rewards = []
        if points >= 500:
            rewards.append({"code": "POINT500", "desc": "₹500 Off", "cost": 500})
        if points >= 1000:
            rewards.append({"code": "POINT1000", "desc": "₹1000 Off", "cost": 1000})

        return {
            "points": points,
            "tier": user.data["loyalty_tier"],
            "available_rewards": rewards,
        }

from fastapi import HTTPException
from app.database import supabase


class RBACService:

    @staticmethod
    def assign_role(
        actor_user_id: str,
        target_user_id: str,
        role: str,
        store_id: str | None = None,
        warehouse_id: str | None = None,
    ):
        # 1️⃣ Actor permission check
        actor_roles = (
            supabase.table("user_roles")
            .select("role")
            .eq("user_id", actor_user_id)
            .execute()
        ).data or []

        actor_role_names = {r["role"] for r in actor_roles}

        if "super_admin" not in actor_role_names and "admin" not in actor_role_names:
            raise HTTPException(403, "Insufficient privileges")

        if role == "admin" and "super_admin" not in actor_role_names:
            raise HTTPException(403, "Only super_admin can assign admin")

        # 2️⃣ Role-specific validation
        if role == "store_manager" and not store_id:
            raise HTTPException(400, "store_id required for store_manager")

        if role == "warehouse_manager" and not warehouse_id:
            raise HTTPException(400, "warehouse_id required for warehouse_manager")

        # 3️⃣ Prevent duplicates
        exists = (
            supabase.table("user_roles")
            .select("id")
            .eq("user_id", target_user_id)
            .eq("role", role)
            .eq("store_id", store_id)
            .eq("warehouse_id", warehouse_id)
            .maybe_single()
            .execute()
        ).data

        if exists:
            raise HTTPException(409, "Role already assigned")

        # 4️⃣ Assign
        res = (
            supabase.table("user_roles")
            .insert({
                "user_id": target_user_id,
                "role": role,
                "store_id": store_id,
                "warehouse_id": warehouse_id,
            })
            .execute()
        )

        return res.data[0]

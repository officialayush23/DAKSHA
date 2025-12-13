from fastapi import HTTPException
from app.database import supabase


class RoleService:

    @staticmethod
    def assign_role(
        admin_id: str,
        user_id: str,
        role: str,
        store_id: str | None = None,
        warehouse_id: str | None = None,
    ):
        # -----------------------------------
        # Validate admin permissions
        # -----------------------------------
        admin = (
            supabase.table("users")
            .select("role")
            .eq("id", admin_id)
            .single()
            .execute()
        ).data

        if not admin:
            raise HTTPException(401, "Invalid admin")

        if admin["role"] not in ["super_admin", "admin"]:
            raise HTTPException(403, "Insufficient privileges")

        # -----------------------------------
        # Role rules
        # -----------------------------------
        scoped_roles = {
            "store_manager": "store_id",
            "warehouse_manager": "warehouse_id",
            "store_operator": "store_id",
            "warehouse_operator": "warehouse_id",
        }

        if role in scoped_roles:
            required = scoped_roles[role]
            if required == "store_id" and not store_id:
                raise HTTPException(400, "store_id required")
            if required == "warehouse_id" and not warehouse_id:
                raise HTTPException(400, "warehouse_id required")

        # -----------------------------------
        # Prevent duplicates
        # -----------------------------------
        existing = (
            supabase.table("user_roles")
            .select("id")
            .eq("user_id", user_id)
            .eq("role", role)
            .eq("store_id", store_id)
            .eq("warehouse_id", warehouse_id)
            .maybe_single()
            .execute()
        ).data

        if existing:
            return {"status": "already_assigned"}

        # -----------------------------------
        # Insert role
        # -----------------------------------
        res = (
            supabase.table("user_roles")
            .insert(
                {
                    "user_id": user_id,
                    "role": role,
                    "store_id": store_id,
                    "warehouse_id": warehouse_id,
                }
            )
            .execute()
        )

        return {
            "status": "assigned",
            "assignment": res.data[0],
        }

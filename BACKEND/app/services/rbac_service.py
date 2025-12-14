# app/services/rbac_service.py
from app.database import supabase
from fastapi import HTTPException


class RBACService:

    @staticmethod
    def assign_role(
        *,
        target_user_id: str,
        role: str,
        store_id: str | None = None,
        warehouse_id: str | None = None,
    ):
        """
        Assign operational role to a user.
        Only operational_role_enum allowed here.
        """

        # Guardrails
        if role in ("customer", "super_admin"):
            raise HTTPException(
                400,
                "Global roles cannot be assigned via this endpoint"
            )

        if role == "store_manager" and not store_id:
            raise HTTPException(400, "store_id required for store_manager")

        if role == "warehouse_manager" and not warehouse_id:
            raise HTTPException(400, "warehouse_id required for warehouse_manager")

        # Prevent duplicates
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
            return exists

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

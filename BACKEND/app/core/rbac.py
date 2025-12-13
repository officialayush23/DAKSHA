from fastapi import Depends, HTTPException, status
from typing import Optional, List
from app.database import supabase
from app.core.auth import get_current_user_id


# --------------------------------------------------
# Fetch role + scoped permissions
# --------------------------------------------------
def get_user_rbac(user_id: str) -> dict:
    user = (
        supabase.table("users")
        .select("id, role")
        .eq("id", user_id)
        .single()
        .execute()
    ).data

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user")

    scoped_roles = (
        supabase.table("user_roles")
        .select("role, store_id, warehouse_id")
        .eq("user_id", user_id)
        .execute()
    ).data or []

    return {
        "user_id": user_id,
        "primary_role": user["role"],   # super_admin, customer, etc.
        "scopes": scoped_roles,
    }


def require_role(*allowed_roles: str):
    def dependency(user_id: str = Depends(get_current_user_id)):
        rbac = get_user_rbac(user_id)

        if rbac["primary_role"] in allowed_roles:
            return rbac

        for s in rbac["scopes"]:
            if s["role"] in allowed_roles:
                return rbac

        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Insufficient permissions"
        )

    return dependency


def require_store_access(store_id_param: str = "store_id"):
    def dependency(
        user_id: str = Depends(get_current_user_id),
        **kwargs
    ):
        store_id = kwargs.get(store_id_param)
        if not store_id:
            raise HTTPException(400, "store_id required")

        rbac = get_user_rbac(user_id)

        if rbac["primary_role"] == "super_admin":
            return rbac

        for scope in rbac["scopes"]:
            if (
                scope["role"] == "store_manager"
                and scope["store_id"] == store_id
            ):
                return rbac

        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No access to this store"
        )

    return dependency


def require_warehouse_access(warehouse_id_param: str = "warehouse_id"):
    def dependency(
        user_id: str = Depends(get_current_user_id),
        **kwargs
    ):
        warehouse_id = kwargs.get(warehouse_id_param)
        if not warehouse_id:
            raise HTTPException(400, "warehouse_id required")

        rbac = get_user_rbac(user_id)

        if rbac["primary_role"] == "super_admin":
            return rbac

        for scope in rbac["scopes"]:
            if (
                scope["role"] == "warehouse_manager"
                and scope["warehouse_id"] == warehouse_id
            ):
                return rbac

        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No access to this warehouse"
        )

    return dependency



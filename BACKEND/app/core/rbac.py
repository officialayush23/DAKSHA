# app/core/rbac.py

from fastapi import Depends, HTTPException, status
from app.database import supabase
from app.core.auth import get_current_user_id


# --------------------------------------------------
# LOAD RBAC CONTEXT
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

    scopes = (
        supabase.table("user_roles")
        .select("role, store_id, warehouse_id")
        .eq("user_id", user_id)
        .execute()
    ).data or []

    return {
        "user_id": user_id,
        "identity": user["role"],  # customer | super_admin
        "scopes": scopes,
    }


# --------------------------------------------------
# ROLE CHECK (GLOBAL + SCOPED)
# --------------------------------------------------
def require_role(*allowed_roles: str):
    def dependency(user_id: str = Depends(get_current_user_id)):
        rbac = get_user_rbac(user_id)

        # super_admin bypass
        if rbac["identity"] == "super_admin":
            return rbac

        # global operational roles (catalog, support, fulfillment)
        for scope in rbac["scopes"]:
            if scope["role"] in allowed_roles:
                return rbac

        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Insufficient permissions"
        )

    return dependency


# --------------------------------------------------
# STORE ACCESS
# --------------------------------------------------
def require_store_access(store_id_param: str = "store_id"):
    def dependency(
        user_id: str = Depends(get_current_user_id),
        **kwargs
    ):
        store_id = kwargs.get(store_id_param)
        if not store_id:
            raise HTTPException(400, "store_id required")

        rbac = get_user_rbac(user_id)

        if rbac["identity"] == "super_admin":
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


# --------------------------------------------------
# WAREHOUSE ACCESS
# --------------------------------------------------
def require_warehouse_access(warehouse_id_param: str = "warehouse_id"):
    def dependency(
        user_id: str = Depends(get_current_user_id),
        **kwargs
    ):
        warehouse_id = kwargs.get(warehouse_id_param)
        if not warehouse_id:
            raise HTTPException(400, "warehouse_id required")

        rbac = get_user_rbac(user_id)

        if rbac["identity"] == "super_admin":
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

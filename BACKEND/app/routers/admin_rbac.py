# app/routers/admin_rbac.py

from fastapi import APIRouter, Depends, HTTPException
from app.core.rbac import require_role
from app.database import supabase
from app.models.rbac import RoleAssignRequest

router = APIRouter(prefix="/admin/rbac", tags=["Admin: RBAC"])


# -------------------------------
# ASSIGN ROLE
# -------------------------------
@router.post("/assign")
async def assign_role(
    payload: RoleAssignRequest,
    _rbac=Depends(require_role("super_admin")),
):
    role = payload.role

    # 🚫 HARD BLOCK GLOBAL IDENTITIES
    if role in ("customer", "super_admin"):
        raise HTTPException(
            400,
            "Global roles cannot be assigned via RBAC"
        )

    scoped_roles = {
        "store_manager": "store_id",
        "warehouse_manager": "warehouse_id",
    }

    if role in scoped_roles:
        required = scoped_roles[role]
        if not getattr(payload, required):
            raise HTTPException(400, f"{required} required for {role}")

    exists = (
        supabase.table("user_roles")
        .select("id")
        .eq("user_id", payload.user_id)
        .eq("role", role)
        .eq("store_id", payload.store_id)
        .eq("warehouse_id", payload.warehouse_id)
        .maybe_single()
        .execute()
    ).data

    if exists:
        raise HTTPException(409, "Role already assigned")

    res = (
        supabase.table("user_roles")
        .insert({
            "user_id": payload.user_id,
            "role": role,
            "store_id": payload.store_id,
            "warehouse_id": payload.warehouse_id,
        })
        .execute()
    )

    return {"status": "assigned", "role": res.data[0]}


# -------------------------------
# REVOKE ROLE
# -------------------------------
@router.delete("/revoke")
async def revoke_role(
    payload: RoleAssignRequest,
    _rbac=Depends(require_role("super_admin")),
):
    supabase.table("user_roles") \
        .delete() \
        .eq("user_id", payload.user_id) \
        .eq("role", payload.role) \
        .eq("store_id", payload.store_id) \
        .eq("warehouse_id", payload.warehouse_id) \
        .execute()

    return {"status": "revoked"}


# -------------------------------
# USER RBAC SNAPSHOT
# -------------------------------
@router.get("/user/{user_id}")
async def list_user_roles(
    user_id: str,
    _rbac=Depends(require_role("super_admin")),
):
    user = (
        supabase.table("users")
        .select("id, full_name, role")
        .eq("id", user_id)
        .single()
        .execute()
    ).data

    roles = (
        supabase.table("user_roles")
        .select("role, store_id, warehouse_id, created_at")
        .eq("user_id", user_id)
        .execute()
    ).data

    return {
        "user": user,
        "operational_roles": roles,
    }


# -------------------------------
# ROLE METADATA (FRONTEND)
# -------------------------------
@router.get("/roles")
async def list_assignable_roles(
    _rbac=Depends(require_role("super_admin")),
):
    return {
        "global_identity": ["customer", "super_admin"],
        "operational_roles": [
            "catalog_admin",
            "support_agent",
            "fulfillment_agent",
            "store_manager",
            "warehouse_manager",
        ],
        "scoped": {
            "store_manager": ["store_id"],
            "warehouse_manager": ["warehouse_id"],
        },
    }

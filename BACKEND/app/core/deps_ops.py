# app/core/deps_ops.py

# app/core/deps_ops.py
from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user_id
from app.core.database import supabase

async def require_ops_user(
    user_id: str = Depends(get_current_user_id)
):
    res = (
        supabase.table("ops_users")
        .select("id, role, is_active")
        .eq("id", user_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ops access required"
        )

    return res.data

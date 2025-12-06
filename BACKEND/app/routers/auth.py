from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.models.auth import LoginWithPhoneRequest
from app.database import supabase
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sync")
async def sync_user_profile(user_id: str = Depends(get_current_user_id)):
    """
    Called by frontend after Supabase email auth.
    Ensures public.users has a row.
    """
    profile = await UserService.ensure_user_exists(user_id)
    return {"user": profile}


@router.post("/login-phone")
async def login_or_register_phone(payload: LoginWithPhoneRequest):
    """
    Optional phone-based login that merges guest cart via RPC.
    """
    res = supabase.rpc(
        "identify_and_merge_user",
        {
            "p_phone_number": payload.phone_number,
            "p_guest_id": payload.guest_id,
        },
    ).execute()

    data = res.data
    if not data or data.get("status") != "success":
        raise HTTPException(
            status_code=400, detail=(data or {}).get("message", "Login failed")
        )

    return {"user_id": data["user_id"]}

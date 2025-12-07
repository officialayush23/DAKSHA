from fastapi import APIRouter, Depends, HTTPException
from app.schemas import UserRegistration, LoginWithPhoneRequest
from app.database import supabase
from app.auth import get_current_user_id
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sync")
async def sync_user_profile(user_id: str = Depends(get_current_user_id)):
    profile = await UserService.ensure_user_exists(user_id)
    return {"user": profile}


@router.post("/login-phone")
async def login_or_register_phone(payload: LoginWithPhoneRequest):
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
            status_code=400,
            detail=(data or {}).get("message", "Login failed"),
        )

    return {"user_id": data["user_id"]}


@router.post("/complete-profile")
async def complete_profile(data: UserRegistration, user_id: str = Depends(get_current_user_id)):
    user_data = {
        "id": user_id,
        "full_name": data.full_name,
        "gender": data.gender,
        "date_of_birth": str(data.date_of_birth),
        "preferred_languages": data.preferred_languages,
        "loyalty_tier": "Bronze",
        "loyalty_points": 0,
        "ai_profile_summary": "New user",
    }

    try:
        profile_response = supabase.table("profiles").upsert(user_data).execute()

        address_data = {
            "user_id": user_id,
            "type": data.address.type,
            "address_line": data.address.address_line,
            "city": data.address.city,
            "pincode": data.address.pincode,
        }

        address_response = supabase.table("addresses").insert(address_data).execute()

        return {
            "status": "success",
            "profile": profile_response.data,
            "address": address_response.data,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

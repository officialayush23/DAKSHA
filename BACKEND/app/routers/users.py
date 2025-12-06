from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.users import UserProfileUpdate, PaymentMethodCreate, UserRegisterRequest
from app.services.user_service import UserService
from app.database import supabase

router = APIRouter(prefix="/users", tags=["Users"])



@router.get("/me")
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    res = (
        supabase.table("users")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return res.data


@router.patch("/me")
async def update_my_profile(
    data: UserProfileUpdate, user_id: str = Depends(get_current_user_id)
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    return await UserService.update_profile(user_id, update_data)


@router.post("/payment-methods")
async def add_payment_method(
    data: PaymentMethodCreate, user_id: str = Depends(get_current_user_id)
):
    return await UserService.add_payment_method(
        user_id, data.gateway_token_id, data.card_last4, data.card_brand
    )


@router.post("/register")
async def register_profile(
    data: UserRegisterRequest, user_id: str = Depends(get_current_user_id)
):
    """
    Called after email auth to capture phone, name, gender, etc.
    """
    # make sure user row exists
    await UserService.ensure_user_exists(user_id)

    update_data = {
        "full_name": data.full_name,
        "phone_number": data.phone_number,
        "gender": data.gender,
        "date_of_birth": data.date_of_birth,
    }
    profile = await UserService.update_profile(user_id, update_data)
    return {"user": profile}

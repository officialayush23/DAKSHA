# app/routers/users.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.users import UserProfileUpdate, PaymentMethodCreate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """
    Returns the current user's profile.
    If the row doesn't exist in public.users yet, it will be created.
    """
    profile = await UserService.ensure_user_exists(user_id)
    return profile


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
    data: UserProfileUpdate, user_id: str = Depends(get_current_user_id)
):
    """
    Called from frontend 'Complete Profile' screen.
    Semantically 'registration', technically it's just an update on public.users.
    """
    # Ensure row exists (in case /auth/sync wasn't called or failed)
    await UserService.ensure_user_exists(user_id)

    update_data = {k: v for k, v in data.dict().items() if v is not None}
    return await UserService.update_profile(user_id, update_data)

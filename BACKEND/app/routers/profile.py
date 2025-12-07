from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.schemas import AddressCreate, StyleProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/")
async def get_profile(user_id: str = Depends(get_current_user_id)):
    return ProfileService.get_profile(user_id)


@router.post("/addresses")
async def add_address(addr: AddressCreate, user_id: str = Depends(get_current_user_id)):
    return {"status": "added", "data": ProfileService.add_address(user_id, addr.dict())}


@router.put("/style")
async def update_style(
    profile: StyleProfileUpdate, user_id: str = Depends(get_current_user_id)
):
    ProfileService.update_style(user_id, profile.dict())
    return {"status": "updated"}

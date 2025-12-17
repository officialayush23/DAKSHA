#   app/routers/home.py

from fastapi import APIRouter, Depends
from app.services.home_service import HomeService
from app.core.auth import get_current_user_optional

router = APIRouter(tags=["Home"])


@router.get("/home")
async def home(user_ctx = Depends(get_current_user_optional)):
    user_id = user_ctx.get("user_id") if user_ctx else None
    return HomeService.get_home(user_id)

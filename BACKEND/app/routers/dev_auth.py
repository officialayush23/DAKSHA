# app/api/v1/endpoints/dev_auth.py

from fastapi import APIRouter
from uuid import uuid4

from app.core.security import create_access_token

router = APIRouter(prefix="/dev", tags=["Dev Auth"])

@router.post("/token")
async def get_dev_token(
    email: str = "dev@finni.ai",
):
    """
    ⚠️ DEV ONLY
    Returns a valid JWT for local testing
    """

    user_id = uuid4()

    token = create_access_token(
        user_id=user_id,
        email=email,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user_id),
    }

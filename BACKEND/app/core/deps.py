# app/core/deps.py
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import  Header
from jose import jwt, JWTError
from app.core.database import SessionLocal
from app.core.security import verify_supabase_jwt
from app.core.auth import get_or_create_user
from app.models.models import User
from app.enums.db_enums import UserRoleEnum

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    """
    Verifies Supabase JWT and syncs user to public.users
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_or_create_user(db, payload)
    return user
def get_current_user_optional(
    # For endpoints that work for both guests and users (e.g. Products)
    # You'll need to update security.py to allow optional tokens if you want strict 'Guest' tracking logic,
    # but usually, guests just hit the API without an Authorization header.
    # For now, let's keep it simple: Public APIs don't use this dependency.
 
):
    pass

def get_current_admin(
    user: User = Depends(get_current_user),
):
    """
    Blocks access unless role is 'admin'.
    """
    if user.role != UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user
# app/core/deps.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
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
    jwt_payload: dict = Depends(verify_supabase_jwt),
    db: Session = Depends(get_db),
):
    """
    Returns the User object. 
    If token is invalid/missing, verify_supabase_jwt raises 401.
    """
    return get_or_create_user(db, jwt_payload)

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
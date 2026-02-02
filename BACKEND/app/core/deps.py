# app/core/deps.py
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import verify_supabase_jwt
from app.core.auth import get_or_create_user


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
    return get_or_create_user(db, jwt_payload)

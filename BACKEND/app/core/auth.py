# app/core/auth.py
import uuid
from sqlalchemy.orm import Session
from app.models.models import User

def get_or_create_user(db: Session, jwt_payload: dict) -> User:
    """
    Mirrors Supabase auth.users → public.users
    This MUST be called on every authenticated request.
    """

    supabase_user_id = uuid.UUID(jwt_payload["sub"])
    email = jwt_payload.get("email")
    phone = jwt_payload.get("phone")
    name = jwt_payload.get("user_metadata", {}).get("name")

    user = db.query(User).filter(User.id == supabase_user_id).first()

    if not user:
        user = User(
            id=supabase_user_id,
            email=email,
            phone=phone,
            name=name,
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # keep profile in sync
        if name and user.name != name:
            user.name = name
        if phone and user.phone != phone:
            user.phone = phone
        db.commit()

    return user

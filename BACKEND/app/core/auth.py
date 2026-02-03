# app/core/auth.py
# app/core/auth.py
import uuid
from sqlalchemy.orm import Session
from app.models.models import User

def get_or_create_user(db: Session, jwt_payload: dict) -> User:
    supabase_user_id = uuid.UUID(jwt_payload["sub"])

    email = jwt_payload.get("email")
    raw_phone = jwt_payload.get("phone")
    phone = raw_phone if raw_phone else None

    name = jwt_payload.get("user_metadata", {}).get("name")

    user = db.query(User).filter(User.id == supabase_user_id).first()

    if not user:
        user = User(
            id=supabase_user_id,
            email=email,
            phone=phone,   # ✅ NULL, not ""
            name=name,
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        updated = False
        if name and user.name != name:
            user.name = name
            updated = True
        if phone != user.phone:
            user.phone = phone
            updated = True
        if updated:
            db.commit()

    return user


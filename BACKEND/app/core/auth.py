# app/core/auth.py
from sqlalchemy.orm import Session
from app.models.models import User
def get_or_create_user(db: Session, jwt_payload: dict):
    supabase_user_id = jwt_payload["sub"]
    email = jwt_payload.get("email")
    phone = jwt_payload.get("phone")

    user = db.query(User).filter(User.id == supabase_user_id).first()

    if not user:
        user = User(
            id=supabase_user_id,
            email=email,
            phone=phone,
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

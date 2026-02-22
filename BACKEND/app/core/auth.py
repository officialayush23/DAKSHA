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
        # Existing user: ONLY sync identity-critical fields (like email).
        # DO NOT sync phone or name from the JWT, as it will overwrite
        # the user's manual profile updates in the database.
        updated = False
        
        if email and user.email != email:
            user.email = email
            updated = True
            
        # The phone and name overwrite logic has been completely removed 
        # from here so the database remains the source of truth.

        if updated:
            db.commit()
            db.refresh(user)

    return user
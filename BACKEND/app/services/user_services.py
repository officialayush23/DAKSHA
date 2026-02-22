# app/services/user_services.py
import uuid
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import func
from geoalchemy2 import WKTElement
from datetime import datetime, timedelta
from app.models.models import UserLocation , LoyaltyLedger
from app.models.models import UserAddress, UserWishlist, UserCard, User , UserPreferences
from app.services.event_service import emit_event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum


# ========== ADDRESS ==========

def add_address(db: Session, user_id: uuid.UUID, payload):
    if payload.is_default:
        db.query(UserAddress).filter(
            UserAddress.user_id == user_id
        ).update({"is_default": False})

    addr = UserAddress(
    user_id=user_id,
    label=payload.label,
    address_line1=payload.address_line1,
    address_line2=payload.address_line2,
    city=payload.city,
    state=payload.state,
    pincode=payload.pincode,
    country="India",
    is_default=payload.is_default,
)
    db.add(addr)
    db.commit()  # NOTE: acceptable for now
    return addr


def get_user_addresses(db: Session, user_id: uuid.UUID):
    return (
        db.query(UserAddress)
        .filter(UserAddress.user_id == user_id)
        .all()
    )

def update_address(db: Session, user_id: uuid.UUID, address_id, payload):
    addr = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == user_id,
    ).first()

    if not addr:
        return None

    data = payload.dict(exclude_unset=True)

    for k, v in data.items():
        setattr(addr, k, v)

    db.commit()
    return addr


# # ========== PROFILE ==========

# def get_user_profile(db: Session, user_id: uuid.UUID):
#     return db.query(User).get(user_id)

# ========== PROFILE ==========

def get_hydrated_user_profile(db: Session, user_id: uuid.UUID) -> dict:
    # 1. Fetch user and eager-load the 1-to-1 relationships
    user = (
        db.query(User)
        .options(
            joinedload(User.preferences),
            joinedload(User.behavior),
            joinedload(User.telegram_info)
        )
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return None

    # 2. Calculate current loyalty points balance
    points_balance = db.query(func.sum(LoyaltyLedger.points)).filter(
        LoyaltyLedger.user_id == user_id
    ).scalar() or 0

    # 3. Format the complete profile payload safely
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "gender": user.gender,
        "loyalty_tier": user.loyalty_tier,
        "points_balance": points_balance,
        
        # Explicit Preferences
        "preferences": {
            "preferred_sizes": user.preferences.preferred_sizes if user.preferences else [],
            "preferred_colors": user.preferences.preferred_colors if user.preferences else [],
            "preferred_categories": user.preferences.preferred_categories if user.preferences else [],
            "excluded_categories": user.preferences.excluded_categories if user.preferences else [],
            "price_min": float(user.preferences.preferred_price_min) if user.preferences and user.preferences.preferred_price_min else None,
            "price_max": float(user.preferences.preferred_price_max) if user.preferences and user.preferences.preferred_price_max else None,
        } if user.preferences else {},
        
        # Implicit Behavior (AI/Analytics)
        "behavior": {
            "most_common_size": user.behavior.most_common_size if user.behavior else None,
            "most_common_color": user.behavior.most_common_color if user.behavior else None,
            "avg_viewed_price": float(user.behavior.avg_viewed_price) if user.behavior and user.behavior.avg_viewed_price else None,
        } if user.behavior else {},
        
        # Integrations
        "telegram_connected": bool(user.telegram_info and user.telegram_info.opt_in)
    }

# ========== CARDS ==========

def add_card(db: Session, user_id: uuid.UUID, payload):
    if payload.is_default:
        db.query(UserCard).filter(
            UserCard.user_id == user_id
        ).update({"is_default": False})

    card = UserCard(user_id=user_id, **payload.dict())
    db.add(card)
    db.commit()
    return card


def get_cards(db: Session, user_id: uuid.UUID):
    return (
        db.query(UserCard)
        .filter(UserCard.user_id == user_id)
        .all()
    )


def delete_card(db: Session, user_id: uuid.UUID, card_id):
    db.query(UserCard).filter(
        UserCard.id == card_id,
        UserCard.user_id == user_id,
    ).delete()
    db.commit()


def update_user_profile(db: Session, user_id: uuid.UUID, payload):
    """
    Handles the database logic for updating core profile and preferences.
    """
    # 1. Fetch the user freshly using the CURRENT database session
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        return None

    data = payload.dict(exclude_unset=True)
    preferences_data = data.pop("preferences", None)

    # 2. Update the fields on the freshly fetched object
    for k, v in data.items():
        if v is not None:
            # Map "" to None so the database stores a proper NULL
            setattr(db_user, k, v if v != "" else None)

    if preferences_data is not None:
        pref = db.query(UserPreferences).filter_by(user_id=user_id).first()
        if not pref:
            pref = UserPreferences(user_id=user_id)
            db.add(pref)
            
        for pk, pv in preferences_data.items():
            setattr(pref, pk, pv)

    # 3. This commit will now successfully write to the database!
    db.commit()
    db.refresh(db_user)
    
    return db_user
LOCATION_TTL_MINUTES = 15  # auto-expire stale GPS


def upsert_user_location(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID | None,
    lng: float,
    lat: float,
):
    """
    Called frequently by frontend.
    Updates location for session.
    """

    point = WKTElement(f"POINT({lng} {lat})", srid=4326)
    expiry = datetime.utcnow() + timedelta(minutes=LOCATION_TTL_MINUTES)

    loc = (
        db.query(UserLocation)
        .filter(UserLocation.session_id == session_id)
        .first()
    )

    if loc:
        loc.location = point
        loc.recorded_at = datetime.utcnow()
        loc.expires_at = expiry
        if user_id:
            loc.user_id = user_id
    else:
        loc = UserLocation(
            session_id=session_id,
            user_id=user_id,
            location=point,
            expires_at=expiry,
        )
        db.add(loc)

    db.commit()
    return loc
# app/services/user_services.py
import uuid
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from datetime import datetime, timedelta
from app.models.models import UserLocation
from app.models.models import UserAddress, UserWishlist, UserCard, User
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


# ========== PROFILE ==========

def get_user_profile(db: Session, user_id: uuid.UUID):
    return db.query(User).get(user_id)


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
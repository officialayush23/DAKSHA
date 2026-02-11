# app/services/user_services.py
import uuid
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement

from app.models.models import UserAddress, UserWishlist, UserCard, User
from app.services.event_service import emit_event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum


# ========== ADDRESS ==========

def add_address(db: Session, user_id: uuid.UUID, payload):
    if payload.is_default:
        db.query(UserAddress).filter(
            UserAddress.user_id == user_id
        ).update({"is_default": False})

    location_geom = None
    if payload.location:
        if isinstance(payload.location, list):
            lng, lat = payload.location
        elif isinstance(payload.location, dict) and "coordinates" in payload.location:
            lng, lat = payload.location["coordinates"]
        else:
            raise ValueError("Invalid location format")

        location_geom = WKTElement(f"POINT({lng} {lat})", srid=4326)

    addr = UserAddress(
        user_id=user_id,
        name=payload.name,
        phone=payload.phone,
        address_line=payload.address_line,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
        type=payload.type,
        is_default=payload.is_default,
        location=location_geom,
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

    # Fix: Handle location update specifically
    if "location" in data:
        loc_data = data.pop("location")
        if loc_data and "coordinates" in loc_data:
            lng, lat = loc_data["coordinates"]
            addr.location = WKTElement(f"POINT({lng} {lat})", srid=4326)

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

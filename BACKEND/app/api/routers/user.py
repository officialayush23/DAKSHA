# app/api/routers/user.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional
import uuid
from app.core.deps import get_db, get_current_user
from app.services.user_services import upsert_user_location
from app.services.session_service import get_active_session
from app.core.deps import get_db, get_current_user
from app.schemas.schemas import (
    WishlistAdd,
    AddressCreate,
    AddressUpdate,
    AddressLocationPatch,
    UserProfileUpdate,
    UserRegisterPayload,
    CardCreate,
    ReviewCreate,
)
from app.models.models import (
    Review,
    UserPreferences,
    UserAddress,
)
from app.services.user_services import (
    add_address,
    update_address,
    get_user_addresses,
    get_user_profile,
    add_card,
    get_cards,
    delete_card,
)

from app.services.wishlist_service import (
    add_to_wishlist,
    remove_from_wishlist,
    list_wishlist,
)
from app.services.event_service import emit_event
from app.services.embedding_service import update_user_preference_summary
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum, ChannelEnum
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

router = APIRouter(prefix="/user", tags=["User"])

# ======================================================
# SEARCH (intent + signal only, NO product logic)
# ======================================================

@router.post("/search")
def search_products(
    payload,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    emit_event(
        db=db,
        event_type=EventTypeEnum.search,
        channel=payload.channel,
        user_id=user.id,
        entity_type=EntityTypeEnum.product,
        metadata={"query": payload.query},
    )

    update_user_preference_summary(db, user.id)

    return {"status": "search_logged"}

# ======================================================
# GENERIC EVENT CAPTURE (frontend/manual)
# ======================================================

@router.post("/event")
def capture_event(
    event_type: EventTypeEnum,
    entity_type: EntityTypeEnum,
    entity_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    emit_event(
        db=db,
        event_type=event_type,
        channel=ChannelEnum.web,
        user_id=user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
    )
    return {"status": "captured"}

# ======================================================
# PREFERENCES
# ======================================================

@router.post("/preferences/recompute")
def recompute_preferences(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    update_user_preference_summary(db, user.id)
    return {"status": "recomputed"}

# ======================================================
# WISHLIST
# ====@router.get("/wishlist")
def my_wishlist(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return list_wishlist(db, user_id=user.id)


@router.post("/wishlist")
def add_wishlist_item(
    payload: WishlistAdd,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    item = add_to_wishlist(
        db=db,
        user_id=user.id,
        product_variant_id=payload.product_variant_id,
        channel=ChannelEnum.web,
    )
    db.commit()
    return item


@router.delete("/wishlist/{variant_id}")
def remove_wishlist_item(
    variant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    removed = remove_from_wishlist(
        db=db,
        user_id=user.id,
        product_variant_id=variant_id,
        channel=ChannelEnum.web,
    )
    db.commit()

    if not removed:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"status": "removed"}

# ======================================================
# ADDRESSES
# ======================================================

@router.post("/addresses")
def add_address_api(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return add_address(db, user.id, payload)


@router.put("/addresses/{address_id}")
def update_address_api(
    address_id: uuid.UUID,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    addr = update_address(db, user.id, address_id, payload)
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    return addr


@router.get("/addresses")
def list_addresses(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_user_addresses(db, user.id)


@router.patch("/addresses/{address_id}/location")
def update_address_location(
    address_id: uuid.UUID,
    payload: AddressLocationPatch,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    address = (
        db.query(UserAddress)
        .filter(
            UserAddress.id == address_id,
            UserAddress.user_id == user.id,
        )
        .first()
    )

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    address.location = from_shape(
        Point(payload.lng, payload.lat),
        srid=4326,
    )

    db.commit()
    return {"status": "updated", "address_id": address.id}

# ======================================================
# PROFILE
# ======================================================

@router.get("/profile")
def my_profile(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_user_profile(db, user.id)


@router.put("/profile")
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    updates = {
        k: v
        for k, v in payload.dict(exclude_unset=True).items()
        if v not in ("", None)
    }

    for k, v in updates.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)

    emit_event(
        db=db,
        event_type=EventTypeEnum.profile_updated,
        channel=ChannelEnum.web,
        user_id=user.id,
        entity_type=EntityTypeEnum.user,
    )

    return user


@router.post("/register")
def register_user(
    payload: UserRegisterPayload,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    user.name = payload.name
    if payload.phone:
        user.phone = payload.phone

    pref = db.query(UserPreferences).filter_by(user_id=user.id).first()
    if not pref:
        db.add(
            UserPreferences(
                user_id=user.id,
                preferred_categories=[],
                preferred_sizes=[],
            )
        )

    db.commit()
    return {"ok": True}

# ======================================================
# CARDS
# ======================================================

@router.get("/cards")
def my_cards(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_cards(db, user.id)


@router.post("/cards")
def add_new_card(
    payload: CardCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return add_card(db, user.id, payload)


@router.delete("/cards/{card_id}")
def remove_card_api(
    card_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    delete_card(db, user.id, card_id)
    return {"status": "deleted"}

# ======================================================
# REVIEWS (post-purchase, allowed here)
# ======================================================

@router.get("/products/{product_id}/reviews")
def get_product_reviews(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id)
        .order_by(desc(Review.created_at))
        .all()
    )

    return [
        {
            "id": r.id,
            "user_name": r.user.name if r.user else "Anonymous",
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at,
        }
        for r in reviews
    ]


@router.post("/reviews")
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    review = Review(
        user_id=user.id,
        product_id=payload.product_id,
        rating=payload.rating,
        comment=payload.comment,
        images=payload.images,
    )
    db.add(review)
    db.commit()

    emit_event(
        db=db,
        event_type=EventTypeEnum.review_created,
        channel=ChannelEnum.web,
        user_id=user.id,
        entity_type=EntityTypeEnum.product,
        entity_id=payload.product_id,
    )

    return {"status": "review_added"}




@router.post("/ping")
def update_location(
    lng: float,
    lat: float,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = get_active_session(db, user_id=user.id)

    if not session:
        return {"status": "no_active_session"}

    upsert_user_location(
        db,
        session_id=session.id,
        user_id=user.id,
        lng=lng,
        lat=lat,
    )

    return {"status": "updated"}
# app/services/wishlist_service.py

import uuid
from sqlalchemy.orm import Session
from typing import Optional

from app.models.models import UserWishlist
from app.services.event_service import emit_event
from app.enums.db_enums import (
    EventTypeEnum,
    EntityTypeEnum,
    ChannelEnum,
)


# ======================================================
# WISHLIST CORE
# ======================================================

def add_to_wishlist(
    db: Session,
    *,
    user_id: uuid.UUID,
    product_variant_id: uuid.UUID,
    channel: ChannelEnum,
    session_id: Optional[uuid.UUID] = None,
) -> UserWishlist:
    """
    Idempotent wishlist add.
    """

    existing = (
        db.query(UserWishlist)
        .filter(
            UserWishlist.user_id == user_id,
            UserWishlist.product_variant_id == product_variant_id,
        )
        .first()
    )

    if existing:
        return existing

    item = UserWishlist(
        user_id=user_id,
        product_variant_id=product_variant_id,
    )
    db.add(item)
    db.flush()

    emit_event(
        db=db,
        event_type=EventTypeEnum.wishlist_add,
        channel=channel,
        user_id=user_id,
        session_id=session_id,
        entity_type=EntityTypeEnum.product_variant,
        entity_id=product_variant_id,
        metadata={"source": "wishlist"},
    )

    return item


def remove_from_wishlist(
    db: Session,
    *,
    user_id: uuid.UUID,
    product_variant_id: uuid.UUID,
    channel: ChannelEnum,
    session_id: Optional[uuid.UUID] = None,
) -> bool:
    item = (
        db.query(UserWishlist)
        .filter(
            UserWishlist.user_id == user_id,
            UserWishlist.product_variant_id == product_variant_id,
        )
        .first()
    )

    if not item:
        return False

    db.delete(item)

    emit_event(
        db=db,
        event_type=EventTypeEnum.wishlist_remove,
        channel=channel,
        user_id=user_id,
        session_id=session_id,
        entity_type=EntityTypeEnum.product_variant,
        entity_id=product_variant_id,
        metadata={"source": "wishlist"},
    )

    return True


def list_wishlist(
    db: Session,
    *,
    user_id: uuid.UUID,
):
    return (
        db.query(UserWishlist)
        .filter(UserWishlist.user_id == user_id)
        .all()
    )

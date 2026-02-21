# app/services/wishlist_service.py

import uuid
from sqlalchemy.orm import Session , joinedload
from typing import Optional

from app.models.models import UserWishlist , ProductVariant
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


def get_hydrated_wishlist(db: Session, user_id: uuid.UUID) -> dict:
    # 1. Fetch items and eager-load the relationships to prevent slow queries
    wishlist_items = (
        db.query(UserWishlist)
        .options(
            joinedload(UserWishlist.variant)
            .joinedload(ProductVariant.product)
        )
        .filter(UserWishlist.user_id == user_id)
        .order_by(UserWishlist.added_at.desc())  # Used added_at as per your model
        .all()
    )

    # 2. Return empty structure if no items found
    if not wishlist_items:
        return {
            "total_items": 0, 
            "items": []
        }

    items_data = []

    for item in wishlist_items:
        # FIX: Access the relationship object, NOT the ID field
        variant = item.variant
        
        # Skip if the variant was deleted or missing
        if not variant:
            continue
            
        product = variant.product
        
        # Grab the primary image (position 1) if it exists
        image_url = None
        if variant.images:
            sorted_images = sorted(variant.images, key=lambda img: img.position)
            image_url = sorted_images[0].image_url if sorted_images else None

        price = float(variant.base_price or 0.0)

        items_data.append({
            "wishlist_id": str(item.id),
            "added_at": item.added_at,  # Changed from created_at to added_at
            "variant_id": str(variant.id),
            "product_id": str(product.id),
            "name": product.name,
            "brand": getattr(product, 'brand', None),
            "color": getattr(variant, 'color', None),
            "size": getattr(variant, 'size', None),
            "base_price": price,
            "image_url": image_url
        })

    return {
        "total_items": len(items_data),
        "items": items_data
    }
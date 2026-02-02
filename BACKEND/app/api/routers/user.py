# app/api/routers/user.py

from fastapi import APIRouter, Depends
from app.schemas.schemas import *
from sqlalchemy.orm import Session
import uuid

from app.core.deps import get_db, get_current_user

from app.services.user_services import *
from app.services.event_service import emit_event
from app.services.embedding_service import update_user_preference_summary
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum

router = APIRouter(prefix="/user", tags=["User"])
@router.post("/search")
def search_products(
    payload: SearchQuery,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 1. Log Event
    emit_event(
        db=db,
        user_id=user.id,
        session_id=None,
        channel=payload.channel,
        event_type=EventTypeEnum.search,
        entity_type=EntityTypeEnum.product,
        reason=payload.query,
        metadata={"source": "search_bar"},
    )

    # 2. Store Intent (Explicit)
    # Note: user_services should have a log_intent function, or direct DB add here
    intent = UserIntent(
        id=uuid.uuid4(),
        user_id=user.id,
        intent_text=payload.query,
        confidence=1.0
    )
    db.add(intent)
    db.commit()

    # 3. Async Profile Update
    update_user_preference_summary(db, user.id)

    return {"status": "search_logged"}

@router.post("/event", response_model=None)
def capture_event(
    event_type: EventTypeEnum,
    entity_type: EntityTypeEnum,
    # FIX: Use uuid.UUID explicitly, not SQLAlchemy's UUID type
    entity_id: Optional[uuid.UUID] = None, 
    reason: Optional[str] = None,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    emit_event(
        db=db,
        user_id=user.id,
        session_id=None,
        channel="web", # Default or extract from headers
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        metadata=metadata,
    )
    return {"status": "captured"}

@router.post("/preferences/recompute")
def recompute_preferences(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    update_user_preference_summary(db, user.id)
    return {"status": "recomputed"}
@router.post("/wishlist")
def add_wishlist(
    payload: WishlistAdd,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return add_to_wishlist(db, user, payload)


@router.delete("/wishlist/{variant_id}", response_model=None)
def remove_wishlist(
    variant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    remove_from_wishlist(db, user, variant_id)
    return {"status": "removed"}

@router.post("/cart/items")
def add_cart_item(
    payload: CartItemAdd,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return add_to_cart(db, user, session_id, payload)


@router.put("/cart/items/{variant_id}")
def update_cart_item(
    variant_id: uuid.UUID,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_variant_id == variant_id
    ).first()
    item.quantity = payload.quantity
    db.commit()
    return cart


@router.delete("/cart/items/{variant_id}")
def remove_cart_item(
    variant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_variant_id == variant_id
    ).delete()
    db.commit()
    return {"status": "removed"}
@router.post("/addresses")
def add_address_api(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return add_address(db, user, payload)


@router.put("/addresses/{address_id}")
def update_address_api(
    address_id: uuid.UUID,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return update_address(db, user, address_id, payload)


@router.get("/addresses")
def list_addresses(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return db.query(UserAddress).filter(UserAddress.user_id == user.id).all()
@router.post("/session/channel")
def update_active_channel(
    channel: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = (
        db.query(Session)
        .filter(Session.user_id == user.id, Session.ended_at.is_(None))
        .first()
    )

    if session:
        session.active_channel = channel
        db.commit()

    return {"status": "updated"}

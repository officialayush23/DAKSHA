# app/services/user_services.py
import uuid
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from app.models.models import *
from app.services.event_service import emit_event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum


# ========== ADDRESS ==========

def add_address(db: Session, user, payload):
    if payload.is_default:
        db.query(UserAddress).filter(
            UserAddress.user_id == user.id
        ).update({"is_default": False})

    location = None
    if payload.location:
        lng, lat = payload.location["coordinates"]
        location = WKTElement(f"POINT({lng} {lat})", srid=4326)

    addr = UserAddress(
        user_id=user.id,
        **payload.dict(exclude={"location"}),
        location=location,
    )
    db.add(addr)
    db.commit()
    return addr


def update_address(db: Session, user, address_id, payload):
    addr = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == user.id
    ).first()

    data = payload.dict(exclude_unset=True)
    if "location" in data:
        lng, lat = data.pop("location")["coordinates"]
        addr.location = WKTElement(f"POINT({lng} {lat})", srid=4326)

    for k, v in data.items():
        setattr(addr, k, v)

    db.commit()
    return addr


# ========== WISHLIST ==========

def add_to_wishlist(db: Session, user, payload):
    item = UserWishlist(
        user_id=user.id,
        product_variant_id=payload.product_variant_id
    )
    db.add(item)
    db.commit()

    emit_event(
        db,
        user.id,
        None,
        None,
        EventTypeEnum.wishlist_add,
        EntityTypeEnum.product_variant,
        payload.product_variant_id,
    )
    return item


def remove_from_wishlist(db: Session, user, variant_id):
    db.query(UserWishlist).filter(
        UserWishlist.user_id == user.id,
        UserWishlist.product_variant_id == variant_id
    ).delete()
    db.commit()


# ========== CART ==========

def get_or_create_cart(db: Session, user, session_id):
    cart = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.session_id == session_id
    ).first()

    if not cart:
        cart = Cart(user_id=user.id, session_id=session_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def add_to_cart(db: Session, user, session_id, payload):
    cart = get_or_create_cart(db, user, session_id)

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_variant_id == payload.product_variant_id
    ).first()

    if item:
        item.quantity += payload.quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_variant_id=payload.product_variant_id,
            quantity=payload.quantity
        )
        db.add(item)

    db.commit()

    emit_event(
        db,
        user.id,
        session_id,
        None,
        EventTypeEnum.add_to_cart,
        EntityTypeEnum.cart,
        cart.id,
        quantity=payload.quantity
    )
    return cart



# ================= PRODUCTS (Frontend) =================
def get_products_with_filters(db: Session, category=None, min_price=None, max_price=None, search=None, limit=50):
    query = db.query(Product).join(ProductVariant).filter(Product.active == True)

    if category:
        query = query.filter(Product.category == category)
    
    if min_price:
        query = query.filter(ProductVariant.base_price >= min_price)
    
    if max_price:
        query = query.filter(ProductVariant.base_price <= max_price)

    if search:
        # Full Text Search via TSVector
        query = query.filter(Product.search_tsv.match(search))

    return query.limit(limit).all()

# ================= IDENTITY & AUTH =================
def upsert_user_identity(db: Session, email: str, name: str, phone: str = None):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=name, phone=phone)
        db.add(user)
    else:
        user.name = name
        if phone: user.phone = phone
    db.commit()
    db.refresh(user)
    return user

def get_user_profile(db: Session, user_id):
    return db.query(User).get(user_id)

# ================= CARDS =================
def add_card(db: Session, user_id, payload):
    if payload.is_default:
        db.query(UserCard).filter(UserCard.user_id == user_id).update({"is_default": False})
    
    card = UserCard(user_id=user_id, **payload.dict())
    db.add(card)
    db.commit()
    return card

def get_cards(db: Session, user_id):
    return db.query(UserCard).filter(UserCard.user_id == user_id).all()

def delete_card(db: Session, user_id, card_id):
    db.query(UserCard).filter(UserCard.id == card_id, UserCard.user_id == user_id).delete()
    db.commit()
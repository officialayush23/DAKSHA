# app/api/routers/proucts.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.services.event_service import emit_event
from app.core.deps import get_db, get_current_user
from app.enums.db_enums import EntityTypeEnum , EventTypeEnum
from app.models.models import ProductVariant, Product
from app.services.pricing_service import resolve_variant_price
from app.enums.db_enums import ChannelEnum
from app.services.session_service import get_active_session
router = APIRouter(prefix="/products", tags=["Products"])

# =========================
# PRODUCT FEED (Variant-wise)
# =========================
@router.get("")
def product_feed(
    category: str | None = None,
    brand: str | None = None,
    gender: str | None = None,
    size: str | None = None,
    color: str | None = None,
    occasion: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = (
        db.query(ProductVariant)
        .join(Product)
        .options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.images),
        )
        .filter(ProductVariant.active.is_(True), Product.active.is_(True))
    )

    if category:
        query = query.filter(Product.category == category)
    if brand:
        query = query.filter(Product.brand == brand)
    if gender:
        query = query.filter(Product.gender == gender)
    if occasion:
        query = query.filter(Product.occasion == occasion)
    if size:
        query = query.filter(ProductVariant.size == size)
    if color:
        query = query.filter(ProductVariant.color == color)
    if min_price:
        query = query.filter(ProductVariant.base_price >= min_price)
    if max_price:
        query = query.filter(ProductVariant.base_price <= max_price)

    variants = query.limit(limit).all()

    out = []
    for v in variants:
        price = resolve_variant_price(db, v)
        out.append({
            "variant_id": v.id,
            "product_id": v.product_id,
            "brand": v.product.brand,
            "category": v.product.category,
            "name": v.product.name,
            "gender": v.product.gender,
            "occasion": v.product.occasion,
            "size": v.size,
            "color": v.color,
            "image": v.images[0].image_url if v.images else None,
            **price,
        })

    return out



# =========================
# HOT DEALS — Variants with active discount rules
# (must be defined BEFORE /{product_id} to avoid route shadowing)
# =========================
@router.get("/discounted")
def discounted_products(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Return active variants that currently have a discount applied (discount_percent > 0)."""
    from datetime import datetime
    from sqlalchemy import or_
    from app.models.models import ProductDiscountRule

    now = datetime.utcnow()

    # Load active discount rules once
    active_rules = db.query(ProductDiscountRule).filter(
        ProductDiscountRule.active.is_(True),
        ProductDiscountRule.valid_from <= now,
        or_(
            ProductDiscountRule.valid_to.is_(None),
            ProductDiscountRule.valid_to >= now,
        ),
    ).all()

    if not active_rules:
        return []

    # Fetch active variants
    variants = (
        db.query(ProductVariant)
        .join(Product)
        .options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.images),
        )
        .filter(ProductVariant.active.is_(True), Product.active.is_(True))
        .all()
    )

    deals = []
    for v in variants:
        price = resolve_variant_price(db, v, rules_cache=active_rules)
        if price["discount_percent"] > 0:
            deals.append({
                "variant_id": v.id,
                "product_id": v.product_id,
                "brand": v.product.brand,
                "category": v.product.category,
                "name": v.product.name,
                "gender": v.product.gender,
                "size": v.size,
                "color": v.color,
                "image": v.images[0].image_url if v.images else None,
                **price,
            })
        if len(deals) >= limit:
            break

    # Sort by highest discount first
    deals.sort(key=lambda x: x["discount_percent"], reverse=True)
    return deals


# =========================
# PRODUCT DETAIL (All variants)
# =========================
@router.get("/{product_id}")
def product_detail(
    product_id,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    product = db.query(Product).get(product_id)
    if not product:
        return None

    variants = (
        db.query(ProductVariant)
        .options(joinedload(ProductVariant.images))
        .filter(
            ProductVariant.product_id == product_id,
            ProductVariant.active.is_(True),
        )
        .all()
    )
    session = get_active_session(
        db, user_id = user.id
    )
    
    emit_event(
    db=db,
    user_id=user.id if user else None,
    session_id=session.id,
    channel=session.active_channel,
    event_type=EventTypeEnum.product_view,
    entity_type=EntityTypeEnum.product,
    entity_id=product_id,
    )

    
   

    return {
        "product_id": product.id,
        "brand": product.brand,
        "category": product.category,
        "gender": product.gender,
        "name": product.name,
        "fabric_type": product.fabric_type,
        "description": product.description,
        "occasion": product.occasion,

        "variants": [
            {
                "variant_id": v.id,
                "sku": v.sku,
                "size": v.size,
                "color": v.color,
                **resolve_variant_price(db, v),
                "images": [img.image_url for img in v.images],
            }
            for v in variants
        ],
    }


# =========================
# SIMILAR PRODUCTS (Same category)
# =========================
@router.get("/{product_id}/similar")
def similar_products(
    product_id,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    product = db.query(Product).get(product_id)
    if not product:
        return []

    return (
        db.query(Product)
        .filter(
            Product.category == product.category,
            Product.id != product.id,
            Product.active.is_(True),
        )
        .limit(limit)
        .all()
    )

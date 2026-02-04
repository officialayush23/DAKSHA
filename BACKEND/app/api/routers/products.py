# app/api/routers/proucts.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.services.event_service import emit_event
from app.core.deps import get_db, get_current_user
from app.enums.db_enums import EntityTypeEnum , EventTypeEnum
from app.models.models import ProductVariant, Product
from app.services.pricing_service import resolve_variant_price
from app.services.session_service import get_or_create_active_session
from app.enums.db_enums import ChannelEnum

router = APIRouter(prefix="/products", tags=["Products"])

# =========================
# PRODUCT FEED (Variant-wise)
# =========================
@router.get("")
def product_feed(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    variants = (
        db.query(ProductVariant)
        .options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.images),
        )
        .filter(ProductVariant.active.is_(True))
        .limit(limit)
        .all()
    )

    out = []
    for v in variants:
        price = resolve_variant_price(db, v)

        out.append({
            "variant_id": v.id,
            "product_id": v.product_id,

            # Product-level info
            "brand": v.product.brand,
            "category": v.product.category,
            "gender": v.product.gender,
            "occasion": v.product.occasion,

            # Variant-level info
            "color": v.color,
            "size": v.size,

            # Media
            "image": v.images[0].image_url if v.images else None,

            # Pricing (base + offer)
            **price,
        })

    return out


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
    session = get_or_create_active_session(
        db, user.id, ChannelEnum.WEB
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

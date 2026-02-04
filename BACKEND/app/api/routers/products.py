# app/api/routers/proucts.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.deps import get_db
from app.models.models import ProductVariant,Product
from app.services.pricing_service import resolve_variant_price

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("")
def product_feed(limit: int = 50, db: Session = Depends(get_db)):
    variants = (
        db.query(ProductVariant)
        .options(joinedload(ProductVariant.product), joinedload(ProductVariant.images))
        .limit(limit)
        .all()
    )

    out = []
    for v in variants:
        price = resolve_variant_price(db, v)
        out.append({
            "variant_id": v.id,
            "product_id": v.product_id,
            "name": v.product.name,
            "image": v.images[0].image_url if v.images else None,
            **price,
        })
    return out

@router.get("/{product_id}/similar")
def similar(product_id, db: Session = Depends(get_db)):
    p = db.query(Product).get(product_id)
    if not p:
        return []

    return (
        db.query(Product)
        .filter(Product.category == p.category, Product.id != p.id)
        .limit(50)
        .all()
    )




@router.get("/{product_id}")
def product_detail(product_id, db: Session = Depends(get_db)):
    variants = (
        db.query(ProductVariant)
        .options(joinedload(ProductVariant.images))
        .filter(ProductVariant.product_id == product_id)
        .all()
    )

    return {
        "product_id": product_id,
        "variants": [
            {
                "variant_id": v.id,
                "sku": v.sku,
                "size": v.size,
                "color": v.color,
                **resolve_variant_price(db, v),
                "images": [i.image_url for i in v.images],
            }
            for v in variants
        ],
    }

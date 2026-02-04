# app/services/resolve_variant_price.py
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Offer, ProductVariant

def resolve_variant_price(db: Session, variant: ProductVariant):
    now = datetime.utcnow()

    offers = (
        db.query(Offer)
        .filter(
            Offer.active == True,
            Offer.valid_from <= now,
            Offer.valid_to >= now,
        )
        .all()
    )

    best = None
    for o in offers:
        if o.eligible_category and o.eligible_category != variant.product.category:
            continue
        if not best or o.discount_value > best.discount_value:
            best = o

    price = variant.base_price
    if best:
        if best.discount_type == "percentage":
            price = price * (1 - best.discount_value / 100)
        else:
            price = max(0, price - best.discount_value)

    return {
        "base_price": variant.base_price,
        "final_price": round(price, 2),
        "offer": best.name if best else None,
    }

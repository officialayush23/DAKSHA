# app/services/copurchase_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import OrderItem, ProductVariant
from app.services.pricing_service import resolve_variant_price
from app.services.impression_service import log_impressions


def get_bought_together(
    db: Session,
    variant_id,
    user_id=None,
    session_id=None,
    limit=10,
):
    subq = (
        db.query(OrderItem.order_id)
        .filter(OrderItem.product_variant_id == variant_id)
        .subquery()
    )

    rows = (
        db.query(
            OrderItem.product_variant_id,
            func.count().label("freq"),
        )
        .filter(
            OrderItem.order_id.in_(subq),
            OrderItem.product_variant_id != variant_id,
        )
        .group_by(OrderItem.product_variant_id)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )

    out = []
    for rank, (vid, _) in enumerate(rows):
        v = db.query(ProductVariant).get(vid)
        if not v:
            continue
        price = resolve_variant_price(db, v)
        out.append({
            "variant_id": v.id,
            "product_id": v.product_id,
            **price,
            "reason": "bought_together",
            "rank": rank,
        })

    log_impressions(db, user_id, out, "checkout", session_id)

    return out

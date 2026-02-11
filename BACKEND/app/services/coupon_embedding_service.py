# app/services/coupon_embedding_service.py
from sqlalchemy.orm import Session
from app.models.models import Coupon, CouponEmbedding
from app.services.embedding_service import generate_text_embedding


def build_coupon_text(c: Coupon) -> str:
    return " | ".join(filter(None, [
        c.code,
        c.description,
        f"type {c.coupon_type}",
        f"value {c.value}",
        f"scope {c.scope}",
        c.scope_value,
    ]))


def upsert_coupon_embedding(db: Session, coupon_id):
    coupon = db.query(Coupon).get(coupon_id)
    if not coupon:
        return

    text = build_coupon_text(coupon)
    vector = generate_text_embedding(text)

    emb = db.query(CouponEmbedding).get(coupon_id)
    if emb:
        emb.embedding = vector
    else:
        db.add(CouponEmbedding(
            coupon_id=coupon_id,
            embedding=vector,
        ))

    db.commit()

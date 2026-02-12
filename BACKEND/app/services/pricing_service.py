# app/services/pricing_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import ProductDiscountRule, ProductVariant
from app.enums.db_enums import CouponTypeEnum

def resolve_variant_price(db: Session, variant: ProductVariant):
    """
    Calculates the final display price based on ACTIVE catalog rules.
    Does NOT apply personalized user offers (those happen at checkout).
    """
    now = datetime.utcnow()

    # 1. Fetch valid rules
    rules = db.query(ProductDiscountRule).filter(
        ProductDiscountRule.active.is_(True),
        ProductDiscountRule.valid_from <= now,
        or_(ProductDiscountRule.valid_to.is_(None), ProductDiscountRule.valid_to >= now)
    ).all()

    best_rule = None
    max_discount_amt = 0.0
    base_price = float(variant.base_price)

    for rule in rules:
        # Check Filters
        if rule.product_ids_filter and variant.id not in rule.product_ids_filter:
            continue
        if rule.category_filter and rule.category_filter != variant.product.category:
            continue
        if rule.brand_filter and rule.brand_filter != variant.product.brand:
            continue

        # Calculate Impact
        current_discount = 0.0
        if rule.discount_type == CouponTypeEnum.percentage:
            current_discount = base_price * (float(rule.value) / 100.0)
        else: # flat
            current_discount = float(rule.value)

        if current_discount > max_discount_amt:
            max_discount_amt = current_discount
            best_rule = rule

    final_price = max(0.0, base_price - max_discount_amt)

    return {
        "base_price": base_price,
        "final_price": round(final_price, 2),
        "discount_percent": float(best_rule.value) if best_rule and best_rule.discount_type == CouponTypeEnum.percentage else 0,
        "offer_name": best_rule.name if best_rule else None,
    }
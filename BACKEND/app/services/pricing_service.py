# app/services/pricing_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import ProductDiscountRule, ProductVariant
from app.enums.db_enums import CouponTypeEnum


def resolve_variant_price(
    db: Session,
    variant=None,
    *,
    variant_id=None,
    base_price=None,
    brand=None,
    category=None,
    rules_cache=None,
):
    """
    UNIVERSAL PRICE RESOLVER

    Supports:
    ✔ resolve_variant_price(db, variant)
    ✔ resolve_variant_price(db, variant_id=..., base_price=..., brand=..., category=...)
    ✔ rules_cache for performance

    This keeps product feed, detail, and ranking fast & compatible.
    """

    now = datetime.utcnow()

    # --------------------------------
    # EXTRACT DATA
    # --------------------------------
    if variant is not None:
        variant_id = variant.id
        base_price = float(variant.base_price)
        brand = variant.product.brand
        category = variant.product.category
    else:
        base_price = float(base_price)

    # --------------------------------
    # LOAD RULES (cached if available)
    # --------------------------------
    if rules_cache is None:
        rules = db.query(ProductDiscountRule).filter(
            ProductDiscountRule.active.is_(True),
            ProductDiscountRule.valid_from <= now,
            or_(
                ProductDiscountRule.valid_to.is_(None),
                ProductDiscountRule.valid_to >= now,
            ),
        ).all()
    else:
        rules = rules_cache

    best_rule = None
    max_discount = 0.0

    # --------------------------------
    # APPLY RULES
    # --------------------------------
    for rule in rules:

        # product filter
        if rule.product_ids_filter:
            if str(variant_id) not in {str(x) for x in rule.product_ids_filter}:
                continue

        # category filter
        if rule.category_filter and rule.category_filter != category:
            continue

        # brand filter
        if rule.brand_filter and rule.brand_filter != brand:
            continue

        # compute discount
        if rule.discount_type == CouponTypeEnum.percentage:
            discount = base_price * (float(rule.value) / 100.0)
        else:
            discount = float(rule.value)

        discount = min(discount, base_price)

        if discount > max_discount:
            max_discount = discount
            best_rule = rule

    final_price = round(base_price - max_discount, 2)

    return {
        "base_price": base_price,
        "final_price": final_price,
        "discount_percent": (
            float(best_rule.value)
            if best_rule and best_rule.discount_type == CouponTypeEnum.percentage
            else round((max_discount / base_price) * 100, 2)
            if max_discount
            else 0
        ),
        "offer_name": best_rule.name if best_rule else None,
    }
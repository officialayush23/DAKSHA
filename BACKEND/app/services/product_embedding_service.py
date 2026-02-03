# app/services/product_embedding_service.py

from sqlalchemy.orm import Session
from app.models.models import Product, ProductVariant, ProductEmbedding
from app.services.embedding_service import generate_embedding


def build_variant_embedding_text(
    product: Product,
    variant: ProductVariant,
) -> str:
    """
    Deterministic semantic description of a product variant.
    """

    price_bucket = (
        "budget" if variant.base_price < 1000 else
        "mid-range" if variant.base_price < 3000 else
        "premium"
    )

    return " | ".join(
        filter(
            None,
            [
                product.brand,
                product.category,
                product.gender,
                product.fabric_type,
                product.occasion,
                product.description,
                f"color {variant.color}",
                f"size {variant.size}",
                f"price {price_bucket}",
            ]
        )
    )


def upsert_product_variant_embedding(
    db: Session,
    variant_id,
):
    """
    Create or update a product variant embedding.
    Called on variant create/update.
    """

    variant = (
        db.query(ProductVariant)
        .join(Product)
        .filter(ProductVariant.id == variant_id)
        .first()
    )

    if not variant:
        return

    text = build_variant_embedding_text(variant.product, variant)
    embedding = generate_embedding(text)

    existing = (
        db.query(ProductEmbedding)
        .filter(ProductEmbedding.product_variant_id == variant.id)
        .first()
    )

    if existing:
        existing.embedding = embedding
    else:
        db.add(
            ProductEmbedding(
                product_variant_id=variant.id,
                embedding=embedding,
            )
        )

    db.commit()

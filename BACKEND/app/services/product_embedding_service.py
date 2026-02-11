# app/services/product_embedding_service.py

from sqlalchemy.orm import Session
from app.models.models import (
    Product,
    ProductVariant,
    ProductImage,
    ProductMultimodalEmbedding
)
from app.enums.db_enums import EmbeddingModalityEnum
from app.services.embedding_service import (
    generate_text_embedding,
    generate_image_embedding
)


def build_variant_text(product: Product, variant: ProductVariant) -> str:
    price_bucket = (
        "budget" if variant.base_price < 1000 else
        "mid-range" if variant.base_price < 3000 else
        "premium"
    )

    return " | ".join(filter(None, [
        product.brand,
        product.category,
        product.gender,
        product.fabric_type,
        product.occasion,
        product.name,
        product.description,
        f"color {variant.color}",
        f"size {variant.size}",
        f"price {price_bucket}",
    ]))


def upsert_variant_text_embedding(db: Session, variant_id):
    variant = (
        db.query(ProductVariant)
        .join(Product)
        .filter(ProductVariant.id == variant_id)
        .first()
    )
    if not variant:
        return

    text = build_variant_text(variant.product, variant)
    vector = generate_text_embedding(text)

    emb = (
        db.query(ProductMultimodalEmbedding)
        .filter_by(
            product_variant_id=variant.id,
            modality=EmbeddingModalityEnum.text,
        )
        .first()
    )

    if emb:
        emb.embedding = vector
    else:
        db.add(ProductMultimodalEmbedding(
            product_variant_id=variant.id,
            modality=EmbeddingModalityEnum.text,
            source="variant_text",
            embedding=vector,
        ))

    db.commit()


def upsert_variant_image_embeddings(db: Session, variant_id):
    images = (
        db.query(ProductImage)
        .filter(ProductImage.product_variant_id == variant_id)
        .all()
    )

    for img in images:
        vector = generate_image_embedding(img.image_url)

        exists = (
            db.query(ProductMultimodalEmbedding)
            .filter_by(
                product_variant_id=variant_id,
                modality=EmbeddingModalityEnum.image,
                source=img.image_url,
            )
            .first()
        )

        if exists:
            continue

        db.add(ProductMultimodalEmbedding(
            product_variant_id=variant_id,
            modality=EmbeddingModalityEnum.image,
            source=img.image_url,
            embedding=vector,
        ))

    db.commit()

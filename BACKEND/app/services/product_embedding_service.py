# app/services/product_embedding_service.py

from sqlalchemy.orm import Session
from app.models.models import (
    Product,
    ProductVariant,
    ProductEmbedding,
)
from app.core.config import settings

from google import genai
from google.genai import types

# Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


def embed_text(text: str) -> list[float]:
    """
    Gemini 768-dim embedding
    """
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        ),
    )
    return response.embeddings[0].values


def build_variant_embedding_text(
    product: Product,
    variant: ProductVariant,
) -> str:
    """
    Deterministic semantic text for variant embedding
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
            ],
        )
    )


def upsert_product_variant_embedding(
    db: Session,
    variant_id,
):
    """
    Create or update embedding for a product variant
    """

    variant = (
        db.query(ProductVariant)
        .join(Product)
        .filter(ProductVariant.id == variant_id)
        .first()
    )

    if not variant:
        return

    product = variant.product

    text = build_variant_embedding_text(product, variant)
    embedding = embed_text(text)

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

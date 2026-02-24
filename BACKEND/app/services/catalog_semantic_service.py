# app/services/catalog_semantic_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import generate_text_embedding
from app.services.embedding_service import generate_image_embedding

def semantic_catalog_search(db: Session, query: str, limit: int = 30):
    """
    Semantic retrieval from product embeddings. for agents to answer things like : wedding dress red in color 
    """

    vec = generate_text_embedding(query)

    rows = db.execute(text("""
        SELECT product_variant_id
        FROM product_multimodal_embeddings
        WHERE modality = 'text'
        ORDER BY embedding <=> CAST(:vec AS vector)
        LIMIT :limit
    """), {"vec": vec, "limit": limit}).fetchall()

    return [str(r[0]) for r in rows]




def search_similar_by_image(db: Session, image_url: str, limit: int = 30):
    """
    Finds visually similar variants using image embeddings.
    """

    vec = generate_image_embedding(image_url)

    rows = db.execute(text("""
        SELECT product_variant_id
        FROM product_multimodal_embeddings
        WHERE modality = 'image'
        ORDER BY embedding <=> CAST(:vec AS vector)
        LIMIT :limit
    """), {
        "vec": vec,
        "limit": limit
    }).fetchall()

    return [str(r[0]) for r in rows]
# app/services/user_image_embedding_service.py
from sqlalchemy.orm import Session
from app.models.models import UserImageEmbedding
from app.services.embedding_service import generate_image_embedding


def create_user_image_embedding(
    db: Session,
    user_id,
    session_id,
    image_url,
    used_for=None,
):
    vector = generate_image_embedding(image_url)

    emb = UserImageEmbedding(
        user_id=user_id,
        session_id=session_id,
        image_url=image_url,
        embedding=vector,
        used_for=used_for,
    )

    db.add(emb)
    db.commit()
    return emb

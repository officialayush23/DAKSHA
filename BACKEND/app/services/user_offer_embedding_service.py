# app/services/user_offer_embedding_service.py
from sqlalchemy.orm import Session
from app.models.models import UserPersonalizedOffer, UserPersonalizedOfferEmbedding
from app.services.embedding_service import generate_text_embedding

def upsert_user_offer_embedding(db: Session, offer_id):
    offer = db.query(UserPersonalizedOffer).get(offer_id)
    if not offer:
        return

    text = f"{offer.offer_name} | {offer.condition_text}"
    vec = generate_text_embedding(text)

    emb = db.query(UserPersonalizedOfferEmbedding).get(offer_id)
    if emb:
        emb.embedding = vec
    else:
        db.add(UserPersonalizedOfferEmbedding(
            offer_id=offer_id,
            embedding=vec,
        ))

    db.commit()

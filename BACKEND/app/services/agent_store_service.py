# app/services/agent_store_service.py
from sqlalchemy.orm import Session
from app.models.models import Store, StoreInventory


def list_stores_with_stock(db: Session):
    stores = db.query(Store).all()
    out = []

    for s in stores:
        stock = (
            db.query(StoreInventory)
            .filter(StoreInventory.store_id == s.id)
            .all()
        )

        out.append({
            "store_id": s.id,
            "name": s.name,
            "city": s.city,
            "state": s.state,
            "active": s.active,
            "stock": [
                {
                    "variant_id": r.product_variant_id,
                    "in_stock": r.in_stock,
                    "reserved": r.reserved_for_pickup,
                }
                for r in stock
            ],
        })

    return out

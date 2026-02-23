# app/api/routers/stores.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.schemas import StoreLookupRequest
from app.services.store_availability_service import (
    get_nearest_stores_with_cart
)

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post("/nearest")
def nearest(data: StoreLookupRequest,
            db: Session = Depends(get_db)):
   return get_nearest_stores_with_cart(
    db,
    data.cart_id,
    data.latitude,
    data.longitude,
)
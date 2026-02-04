
# app/api/routers/checkout.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.services.pickup_store_service import get_pickup_eligible_stores
from app.services.checkout_facade import start_or_resume_checkout, get_checkout
from app.services.session_service import get_or_create_active_session
from app.enums.db_enums import ChannelEnum

router = APIRouter(prefix="/checkout", tags=["Checkout"])

@router.post("/start")
def checkout_start(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = get_or_create_active_session(
        db, user.id, ChannelEnum.web
    )

    checkout = start_or_resume_checkout(
        db=db,
        user_id=user.id,
        session_id=session.id,
    )

    return {
        "checkout_id": checkout.id,
        "state": checkout.state,
        "reserved_until": checkout.reserved_until,
    }

@router.get("/{checkout_id}")
def checkout_status(
    checkout_id: UUID,
    db: Session = Depends(get_db),
):
    checkout = get_checkout(db, checkout_id)
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")

    return {
        "checkout_id": checkout.id,
        "state": checkout.state,
        "locked_price": checkout.locked_price,
        "reserved_until": checkout.reserved_until,
        "payment_attempts": checkout.payment_attempts,
        "last_error": checkout.last_error,
    }

@router.get("/pickup/stores")
def pickup_store_options(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: int = Query(15),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = get_or_create_active_session(
        db, user.id, ChannelEnum.web
    )

    return get_pickup_eligible_stores(
        db=db,
        user_id=user.id,
        session_id=session.id,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
    )

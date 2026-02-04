# app/routers/support.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.services.support_service import create_return, create_exchange
from app.services.admin_services import create_complaint

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/returns")
def request_return(payload, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return create_return(db, payload)


@router.post("/exchanges")
def request_exchange(payload, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return create_exchange(db, payload)


@router.post("/complaints")
def file_complaint(payload, db: Session = Depends(get_db), user=Depends(get_current_user)):
    payload.user_id = user.id
    return create_complaint(db, payload)

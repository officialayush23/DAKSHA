# app/api/routers/admin_kiosk.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.services.admin_services import create_kiosk, list_kiosks

router = APIRouter(prefix="/admin/kiosks", tags=["Admin – Kiosk"])

@router.post("")
def create(payload, db: Session = Depends(get_db)):
    return create_kiosk(db, payload)

@router.get("")
def list_all(db: Session = Depends(get_db)):
    return list_kiosks(db)

# app/api/routers/admin_kiosk.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_admin
from app.schemas.schemas import KioskCreate
from app.services.admin_services import create_kiosk, list_kiosks

router = APIRouter(prefix="/admin/kiosks", tags=["Admin – Kiosk"])

@router.post("")   # ← this is OK because prefix already ends with /kiosks
def create(
    payload: KioskCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),   # ✅ REQUIRED
):
    return create_kiosk(db, payload)

@router.get("")
def list_all(
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    return list_kiosks(db)

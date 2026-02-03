# app/api/routers/admin_chat.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_admin
from app.services.admin_services import active_handoffs

router = APIRouter(prefix="/admin/chat", tags=["Admin Chat"])

@router.get("/handoffs")
def get_active_handoffs(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    return active_handoffs(db)

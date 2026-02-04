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


from app.models.models import Conversation

@router.post("/message/{session_id}")
def admin_send(
    session_id,
    message: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    db.add(
        Conversation(
            session_id=session_id,
            speaker="admin",
            message=message,
        )
    )
    db.commit()
    return {"sent": True}

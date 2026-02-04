# app/api/routers/loyalty.py
from fastapi import Depends,APIRouter
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.schemas.schemas import *
from app.services.admin_services import *
from uuid import UUID

router = APIRouter(prefix="/loyalty", tags=["loyalty"])

@router.get("/points")
def points(db: Session = Depends(get_db), user=Depends(get_current_user)):
    total = (
        db.query(func.sum(LoyaltyTransaction.points))
        .filter(LoyaltyTransaction.user_id == user.id)
        .scalar()
    )
    return {"points": total or 0}

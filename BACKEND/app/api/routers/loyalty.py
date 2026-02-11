# app/api/routers/loyalty.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, get_channel
from app.services.loyalty_service import (
    get_balance,
)
from app.enums.db_enums import ChannelEnum

router = APIRouter(prefix="/loyalty", tags=["Loyalty"])


@router.get("/summary")
def loyalty_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return {
        "points": get_balance(db, user.id),
        "tier": user.loyalty_tier,
    }

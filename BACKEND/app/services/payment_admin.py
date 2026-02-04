# app/services/payment_admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_admin
from app.models.models import PaymentGatewayConfig

router = APIRouter(prefix="/admin/payment", tags=["Admin Payment"])

@router.get("/toggle")
def get_toggle(db: Session = Depends(get_db)):
    cfg = db.query(PaymentGatewayConfig).get(1)
    return {"force_status": cfg.force_status if cfg else None}

@router.patch("/toggle")
def set_toggle(
    status: str | None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    cfg = db.query(PaymentGatewayConfig).get(1)
    if not cfg:
        cfg = PaymentGatewayConfig(id=1, force_status=status)
        db.add(cfg)
    else:
        cfg.force_status = status
    db.commit()
    return {"force_status": cfg.force_status}

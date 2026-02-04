# app/services/payment_admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_admin
from app.services.payment_gateway_config_service import (
    get_gateway_config,
    update_gateway_config,
)

router = APIRouter(prefix="/admin/payment-gateway", tags=["Admin"])


@router.get("")
def get_config(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    cfg = get_gateway_config(db)
    return {
        "force_status": cfg.force_status,
        "updated_at": cfg.updated_at,
    }


@router.post("")
def set_config(
    force_status: str | None,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    cfg = update_gateway_config(db, force_status=force_status)
    return {
        "force_status": cfg.force_status,
        "updated_at": cfg.updated_at,
    }

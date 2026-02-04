# app/services/payment_gateway_config_service.py
from sqlalchemy.orm import Session
from app.models.models import PaymentGatewayConfig

SINGLETON_ID = 1


def get_gateway_config(db: Session) -> PaymentGatewayConfig:
    """
    The ONLY read entry point.
    """
    cfg = db.get(PaymentGatewayConfig, SINGLETON_ID)

    if not cfg:
        cfg = PaymentGatewayConfig(id=SINGLETON_ID)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    return cfg


def update_gateway_config(
    db: Session,
    *,
    force_status: str | None,
) -> PaymentGatewayConfig:
    """
    The ONLY write entry point.
    """
    cfg = get_gateway_config(db)
    cfg.force_status = force_status
    db.commit()
    db.refresh(cfg)
    return cfg

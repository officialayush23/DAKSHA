# app/services/payment_gateway_config_service.py
from sqlalchemy.orm import Session
from app.models.models import PaymentGatewayConfig

from sqlalchemy.orm import Session
from app.models.models import PaymentGatewayConfig


def get_gateway_config(db: Session) -> PaymentGatewayConfig:
    config = db.get(PaymentGatewayConfig, 1)

    if not config:
        config = PaymentGatewayConfig(id=1, force_status=None)
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


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

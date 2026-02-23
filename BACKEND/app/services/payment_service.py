# app/services/payment_service.py
import uuid
from sqlalchemy.orm import Session
from app.models.models import Payment
from app.enums.db_enums import PaymentStatusEnum
from app.services.payment_gateway_config_service import get_gateway_config


def process_payment(
    db: Session,
    *,
    checkout_id,
    order_id=None,
    amount: float,
    method: str = "card",
    agent_run_id=None,
):
    """
    Deterministic payment processor.

    Uses payment_gateway_config.force_status to simulate gateway outcome.
    """

    config = get_gateway_config(db)

    if config.force_status == "fail":
        status = PaymentStatusEnum.failed
        failure_reason = "Forced failure by gateway config"
        success = False
    else:
        status = PaymentStatusEnum.success
        failure_reason = None
        success = True

    payment = Payment(
        checkout_id=checkout_id,
        order_id=order_id,
        method=method,
        status=status,
        failure_reason=failure_reason,
        idempotency_key=str(uuid.uuid4()),
        agent_run_id=agent_run_id,
    )

    db.add(payment)
    db.flush()

    return success, payment
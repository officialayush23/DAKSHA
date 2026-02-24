# app/api/routers/fulfillment.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.deps import get_db, get_current_user, get_current_admin
from app.services.fulfillment_agent_service import (
    handle_delivery_failure,
    reschedule_delivery,
    handle_missed_pickup,
    reschedule_pickup,
)

router = APIRouter(prefix="/fulfillment", tags=["Fulfillment"])


@router.post("/orders/{order_id}/reschedule-delivery")
async def reschedule_delivery_api(
    order_id: UUID,
    new_address: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return await reschedule_delivery(db, order_id, new_address)


@router.post("/orders/{order_id}/pickup-missed")
async def report_missed_pickup(
    order_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    return await handle_missed_pickup(db, order_id, reason)



@router.post("/orders/{order_id}/reschedule-pickup")
async def reschedule_pickup_api(
    order_id: UUID,
    new_time: datetime,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return await reschedule_pickup(db, order_id, new_time)
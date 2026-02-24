# app/api/routers/post_purchase.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.deps import get_db, get_current_admin
from app.services.post_purchase_agent_service import (
    request_feedback_from_user,
)

router = APIRouter(prefix="/post-purchase", tags=["Post Purchase"])



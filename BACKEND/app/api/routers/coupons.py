# app/api/routers/coupons.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.schemas.schemas import ApplyCouponRequest
from app.services.coupon_service import get_eligible_coupons
from app.services.coupon_service import apply_coupon

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.post("/eligible")
def eligible(data: dict,
             db: Session = Depends(get_db),
             user=Depends(get_current_user)):
    return get_eligible_coupons(
        db,
        user.id,
        data["cart_total"],
        set(data.get("categories", [])),
    )


@router.post("/apply")
def apply(data: ApplyCouponRequest,
          db: Session = Depends(get_db),
          user=Depends(get_current_user)):
    from fastapi import HTTPException
    try:
        # cart_total from the client is ignored; the server's locked price is used
        return {"discount": apply_coupon(db, data.checkout_id, data.coupon_code, data.personal_offer_id, user_id=user.id)}
    except ValueError as e:
        raise HTTPException(400, str(e))
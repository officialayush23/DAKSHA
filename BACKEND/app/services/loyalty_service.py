# app/services/loyalty_service.py
from app.models.models import LoyaltyTransaction

def credit_loyalty_points(db, user_id, order_total):
    points = int(order_total // 100)  # ₹100 = 1 point
    txn = LoyaltyTransaction(
        user_id=user_id,
        points=points,
        source="order"
    )
    db.add(txn)
    db.commit()
    return points

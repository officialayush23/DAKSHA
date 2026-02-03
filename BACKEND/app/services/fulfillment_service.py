# app/services/fulfillment_service.py
from app.models.models import Shipment, Pickup

def create_shipment(db, payload):
    shipment = Shipment(**payload.dict())
    db.add(shipment)
    db.commit()
    return shipment

def create_pickup(db, payload):
    pickup = Pickup(**payload.dict())
    db.add(pickup)
    db.commit()
    return pickup

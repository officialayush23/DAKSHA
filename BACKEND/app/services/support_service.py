# app/services/support_service.py
from app.models.models import Return, Exchange

def create_return(db, payload):
    ret = Return(**payload.dict(), status="initiated")
    db.add(ret)
    db.commit()
    return ret

def create_exchange(db, payload):
    exc = Exchange(**payload.dict(), status="initiated")
    db.add(exc)
    db.commit()
    return exc

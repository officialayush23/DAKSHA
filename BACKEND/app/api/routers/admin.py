# app/api/routers/admin_stores.py
from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.schemas.schemas import *
from app.services.admin_services import *
from uuid import UUID

router = APIRouter(prefix="/admin", tags=["Admin"])

# -------- PRODUCTS --------
@router.post("/products")
def create_prod(p: ProductCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return create_product(db, p)

@router.put("/products/{id}")
def update_prod(id: UUID, p: ProductUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return update_product(db, id, p)

@router.delete("/products/{id}")
def delete_prod(id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    delete_product(db, id)
    return {"status": "deleted"}

# -------- VARIANTS --------
@router.post("/variants")
def create_var(v: VariantCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return create_variant(db, v)

@router.put("/variants/{id}")
def update_var(id: UUID, v: VariantUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return update_variant(db, id, v)

@router.delete("/variants/{id}")
def delete_var(id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    delete_variant(db, id)
    return {"status": "deleted"}

@router.post("/variants/{id}/images")
def add_image(id: UUID, p: VariantImageCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return add_variant_image(db, id, p)

# -------- STORES --------
@router.post("/stores")
def create_st(s: StoreCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return create_store(db, s)

@router.put("/stores/{id}")
def update_st(id: UUID, s: StoreUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return update_store(db, id, s)

@router.get("/stores/{id}/kpis")
def store_stats(id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return store_kpis(db, id)

# -------- INVENTORY --------
@router.post("/inventory/global")
def global_inv(p: AssignGlobalInventory, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return assign_global_inventory(db, p)

@router.post("/inventory/store")
def store_inv(p: AssignStoreInventory, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return assign_store_inventory(db, p)

@router.get("/inventory/kpis")
def inventory_kpis(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return global_inventory_kpis(db)

# -------- PICKUPS --------
@router.put("/pickups/{id}")
def update_pickup(id: UUID, p: PickupStatusUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return update_pickup_status(db, id, p)

# -------- HANDOFFS --------
@router.get("/handoffs")
def handoffs(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return active_handoffs(db)

# -------- COMPLAINTS --------
@router.get("/complaints")
def complaints(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return list_complaints(db)

@router.put("/complaints/{id}")
def update_comp(id: UUID, p: ComplaintStatusUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return update_complaint(db, id, p)

# -------- OFFERS --------
@router.post("/offers")
def create_off(p: OfferCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return create_offer(db, p)

@router.put("/offers/{id}")
def update_off(id: UUID, p: OfferUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return update_offer(db, id, p)

@router.delete("/offers/{id}")
def delete_off(id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    delete_offer(db, id)
    return {"status": "deleted"}

# -------- DELIVERY --------
@router.put("/orders/{id}/status")
def update_delivery(id: UUID, p: OrderStatusUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return update_order_status(db, id, p)

@router.get("/products")
def list_products(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    return get_all_products(db, limit, offset)

@router.get("/products/{id}/variants")
def list_variants(id: uuid.UUID, db: Session = Depends(get_db)):
    return get_product_variants(db, id)

@router.get("/stores")
def list_stores(db: Session = Depends(get_db)):
    return get_all_stores(db)

@router.get("/stores/{id}/pickups")
def list_store_pickups(id: uuid.UUID, db: Session = Depends(get_db)):
    return get_store_pickups(db, id)

@router.get("/inventory/global/{product_id}")
def view_global_inventory(product_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_global_inventory(db, product_id)

@router.get("/inventory/store/{store_id}/{product_id}")
def view_store_inventory(store_id: uuid.UUID, product_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_store_inventory(db, store_id, product_id)

@router.get("/offers")
def list_offers(db: Session = Depends(get_db)):
    return get_all_offers(db)

@router.get("/orders/{id}")
def view_delivery(id: uuid.UUID, db: Session = Depends(get_db)):
    return get_delivery_details(db, id)
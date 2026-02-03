# app/agents/tools.py

import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from geoalchemy2.functions import ST_Distance
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from app.services.checkout_service import (
    start_checkout, resume_checkout, initiate_payment
)
from app.services.recommendation_service import get_hybrid_recommendations
from app.services.admin_services import get_store_inventory, list_offers
from app.models.models import Order, Pickup, Complaint, Store, Cart, CartItem
from app.enums.db_enums import OrderStatusEnum
from app.services.user_services import add_to_cart, add_address, get_or_create_cart
from app.schemas.schemas import CartItemAdd, AddressCreate
from app.services.personalized_offer_service import get_personalized_offer
class AgentTools:
    def __init__(self, db: Session, user_id: uuid.UUID, session_id: uuid.UUID):
        self.db = db
        self.user_id = user_id
        self.session_id = session_id

    # --- DISCOVERY & SEARCH ---
    def get_fashion_recommendations(self, query: str):
        """Use when user asks for suggestions, fashion advice, or searches for products."""
        return get_hybrid_recommendations(self.db, str(self.user_id), intent_text=query)

    def find_nearest_stores(self, latitude: float, longitude: float, radius_km: int = 15):
        """Finds physical AB Fashion stores near the user's current coordinates."""
        user_point = from_shape(Point(longitude, latitude), srid=4326)
        stores = self.db.query(Store).filter(
            ST_Distance(Store.location, user_point) <= radius_km * 1000
        ).order_by(ST_Distance(Store.location, user_point)).limit(5).all()
        
        return [{"name": s.name, "address": s.address, "city": s.city, "id": str(s.id)} for s in stores]

    # --- TRANSACTIONAL (CART & CHECKOUT) ---
    def view_my_cart(self):
        """Returns all items currently in the user's shopping cart with quantities."""
        cart = self.db.query(Cart).filter(Cart.user_id == self.user_id).first()
        if not cart or not cart.items:
            return "Your cart is currently empty."
        return [{"product": i.variant.sku, "quantity": i.quantity, "price": str(i.variant.base_price)} for i in cart.items]

    def add_item_to_cart(self, product_variant_id: str, quantity: int = 1):
        """Adds a specific fashion item to the user's cart."""
        payload = CartItemAdd(product_variant_id=uuid.UUID(product_variant_id), quantity=quantity)
        add_to_cart(self.db, self.user_id, self.session_id, payload)
        return f"Successfully added {quantity} item(s) to your cart."

    def update_shipping_address(self, address_line1: str, city: str, state: str, pincode: str):
        """Updates the user's primary delivery address."""
        payload = AddressCreate(label="Home", address_line1=address_line1, city=city, state=state, pincode=pincode, is_default=True)
        add_address(self.db, self.user_id, payload)
        return "Shipping address updated successfully."

    # --- POST-PURCHASE & SUPPORT ---
    def list_my_orders(self, limit: int = 5):
        """Returns a list of recent orders, their totals, and current delivery/pickup status."""
        orders = self.db.query(Order).filter(Order.user_id == self.user_id).order_by(desc(Order.created_at)).limit(limit).all()
        return [{"order_id": str(o.id), "status": o.order_status, "total": str(o.total_amount), "date": str(o.created_at)} for o in orders]

    def get_order_details(self, order_id: str):
        """Detailed view of a specific order, including tracking status and delivery address."""
        order = self.db.query(Order).filter(Order.id == uuid.UUID(order_id)).first()
        if not order: return "Order not found."
        return {"status": order.order_status, "items": [i.product_variant_id for i in order.items], "address": order.delivery_address}

    def list_my_complaints(self):
        """View status of all past and current support tickets or complaints."""
        complaints = self.db.query(Complaint).filter(Complaint.user_id == self.user_id).all()
        return [{"id": str(c.id), "category": c.category, "status": c.status, "description": c.description} for c in complaints]

    def raise_new_complaint(self, category: str, description: str, order_id: Optional[str] = None):
        """Logs a new formal complaint for a specific order or general issue."""
        complaint = Complaint(
            user_id=self.user_id, order_id=uuid.UUID(order_id) if order_id else None,
            category=category, description=description, status="open"
        )
        self.db.add(complaint)
        self.db.commit()
        return f"Complaint #{complaint.id} has been logged. Our team will review it."

    # --- INVENTORY & OFFERS ---
    def check_local_store_stock(self, store_id: str, variant_id: str):
        """Checks if a specific store has an item in stock for immediate pickup."""
        return get_store_inventory(self.db, uuid.UUID(store_id), uuid.UUID(variant_id))

    def get_available_offers(self):
        """Returns all current valid promotional offers and coupons."""
        return list_offers(self.db)
    
    def get_special_offer_for_product(self, variant_id: str):
        return get_personalized_offer(
            self.db,
            self.user_id,
            uuid.UUID(variant_id)
        )
    def start_checkout(self):
        cart = get_or_create_cart(self.db, self.user_id, self.session_id)
        checkout = start_checkout(self.db, self.user_id, cart.id)
        return {
            "checkout_id": str(checkout.id),
            "state": checkout.state
        }

    def retry_payment(self, checkout_id: str, method: str):
        checkout = resume_checkout(self.db, uuid.UUID(checkout_id))
        initiate_payment(self.db, checkout, method)
        return {
            "state": checkout.state,
            "attempts": checkout.payment_attempts
        }

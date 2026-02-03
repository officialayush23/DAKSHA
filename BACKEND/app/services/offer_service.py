# app/services/offer_service.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.models import Offer, Product, ProductVariant

def attach_offers_to_products(db: Session, products: list):
    """
    Decorates a list of product dictionaries with the best eligible offer.
    """
    now = datetime.now()
    
    # 1. Fetch active offers
    active_offers = db.query(Offer).filter(
        Offer.active == True,
        Offer.valid_from <= now,
        Offer.valid_to >= now
    ).all()

    if not active_offers:
        return products

    # 2. Map Offers by Category (Simplest matching logic)
    category_offers = {}
    for off in active_offers:
        if off.eligible_category:
            if off.eligible_category not in category_offers:
                category_offers[off.eligible_category] = []
            category_offers[off.eligible_category].append(off)

    # 3. Decorate
    for p in products:
        cat = p.get('category') 
        price = p.get('price', 0)
        
        best_offer = None
        
        # Check offers for this category
        if cat in category_offers:
            for off in category_offers[cat]:
                # Check constraints
                if price >= off.min_cart_value:
                    # Logic: Pick offer with highest discount value (simplified)
                    if best_offer is None or off.discount_value > best_offer.discount_value:
                        best_offer = off
        
        if best_offer:
            p['offer'] = {
                "id": str(best_offer.id),
                "name": best_offer.name,
                "label": f"{best_offer.discount_value}% OFF" if best_offer.discount_type == 'percentage' else f"Flat {best_offer.discount_value} OFF"
            }
        else:
            p['offer'] = None

    return products
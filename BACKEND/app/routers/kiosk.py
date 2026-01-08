# app/routers/kiosk.py
from fastapi import APIRouter, Depends, HTTPException, Body
from app.core.database import supabase
from app.core.auth import get_current_user_id
from app.services.commerce_service import CommerceService
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/kiosk", tags=["Kiosk & Store Guide"])

# --- MODELS ---

class KioskHealthReport(BaseModel):
    kiosk_device_id: str
    error_type: Optional[str] = "heartbeat" # 'hardware', 'network', 'heartbeat'

class KioskSessionStart(BaseModel):
    kiosk_device_id: str
    user_id: str # In real deployment, this might come from a QR scan token

class KioskAddRequest(BaseModel):
    variant_id: str
    quantity: int = 1
    store_id: str
    kiosk_device_id: str

class ChatRequest(BaseModel):
    message: str
    store_id: str
    kiosk_device_id: str
    session_id: Optional[str] = None # To continue a specific chat_session

# ---------------------------------------------------------
# 🏥 KIOSK HEALTH & LOGS
# ---------------------------------------------------------
@router.post("/health")
async def report_kiosk_health(payload: KioskHealthReport):
    """
    Logs heartbeat or errors from the physical device.
    """
    try:
        supabase.table("kiosk_health_logs").insert({
            "kiosk_device_id": payload.kiosk_device_id,
            "error_type": payload.error_type,
            "logged_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        return {"status": "ok"}
    except Exception as e:
        print(f"Health Log Error: {e}")
        # Don't crash the kiosk for a log failure
        return {"status": "logging_failed"}

# ---------------------------------------------------------
# 🔑 SESSION MANAGEMENT (Login/Logout)
# ---------------------------------------------------------
@router.post("/session/start")
async def start_kiosk_session(payload: KioskSessionStart):
    """
    Activates a user session on a specific Kiosk Device.
    """
    try:
        # 1. Deactivate any existing active sessions for this device
        # (Constraint: idx_active_kiosk_single_session)
        supabase.table("active_kiosk_sessions")\
            .update({"is_active": False})\
            .eq("kiosk_device_id", payload.kiosk_device_id)\
            .eq("is_active", True)\
            .execute()

        # 2. Create new session (Expires in 30 mins)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        
        res = supabase.table("active_kiosk_sessions").insert({
            "kiosk_device_id": payload.kiosk_device_id,
            "user_id": payload.user_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "is_active": True
        }).select().execute()

        return {"status": "started", "session": res.data[0]}

    except Exception as e:
        raise HTTPException(500, f"Session Start Error: {str(e)}")

@router.post("/session/end")
async def end_kiosk_session(kiosk_device_id: str):
    """
    Logs out the user from the kiosk.
    """
    try:
        supabase.table("active_kiosk_sessions")\
            .update({"is_active": False})\
            .eq("kiosk_device_id", kiosk_device_id)\
            .execute()
        return {"status": "ended"}
    except Exception:
        return {"status": "error"}

# ---------------------------------------------------------
# 🛒 CART ACTIONS
# ---------------------------------------------------------
@router.post("/cart/add")
async def kiosk_add_to_cart(
    payload: KioskAddRequest,
    user_id: str = Depends(get_current_user_id)
):
    try:
        # 1. Log Context to Chat/Omni Session if possible
        # (Skipping for brevity, but you'd insert into conversation_sessions here if needed)

        # 2. Add to Cart
        return await CommerceService.add_to_cart(
            user_id=user_id,
            variant_id=payload.variant_id,
            fulfillment_location_id=None,
            qty=payload.quantity
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/cart/map/{store_id}")
async def map_user_cart(store_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        # 1. Get Cart
        cart_snapshot = CommerceService.get_cart_snapshot(user_id)
        if not cart_snapshot or not cart_snapshot.get('items'):
            return []

        # 2. Get Location
        store = supabase.table("stores").select("fulfillment_location_id").eq("id", store_id).maybe_single().execute()
        if not store or not store.data:
            # Fallback: Return items without location
            return [{**item, "aisle": None, "shelf": None} for item in cart_snapshot['items']]
            
        fl_id = store.data.get('fulfillment_location_id')

        # 3. Enrich
        enriched_items = []
        for item in cart_snapshot['items']:
            inv = supabase.table("inventory").select("aisle_number, shelf_height, bay_number, quantity_on_hand")\
                .eq("fulfillment_location_id", fl_id)\
                .eq("product_variant_id", item['variant_id'])\
                .maybe_single().execute()
            
            loc = inv.data if (inv and inv.data) else {}
            
            enriched_items.append({
                "product_name": item['product_name'],
                "variant_name": item.get('variant_name'),
                "image": item['image_url'],
                "price": item['price'],
                "cart_qty": item['quantity'],
                "aisle": loc.get('aisle_number'),
                "shelf": loc.get('shelf_height'),
                "bay": loc.get('bay_number'),
                "in_stock": (loc.get('quantity_on_hand', 0) >= item['quantity'])
            })

        return enriched_items
    except Exception as e:
        print(f"Cart Map Error: {e}")
        return []

# ---------------------------------------------------------
# 🗣️ INTELLIGENT STORE AGENT (Using conversation_sessions)
# ---------------------------------------------------------
@router.post("/chat")
async def kiosk_chat_agent(payload: ChatRequest, user_id: str = Depends(get_current_user_id)):
    """
    Handles User query + Updates `conversation_sessions`.
    """
    try:
        query = payload.message.lower()
        
        # 1. Get/Create Chat Session
        session_id = payload.session_id
        if not session_id:
            # Create new session if one isn't provided
            session_data = {
                "user_id": user_id,
                "summary": f"Kiosk Interaction: {query[:50]}...",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "entry_channel": "kiosk",  # DB enum: web, mobile, whatsapp, kiosk, voice, admin
                "entry_channel_id": payload.kiosk_device_id,
                "sentiment_trend": 0.0
            }
            # Use conversation_sessions table (matches DB schema)
            new_sess = supabase.table("conversation_sessions").insert({
                "user_id": user_id,
                "started_from": "kiosk",  # DB enum: web, mobile, whatsapp, kiosk, voice, admin
                "summary": f"Kiosk Interaction: {query[:50]}...",
                "status": "active",
                "state": {},
                "state_version": 1
            }).select().execute()
            session_id = new_sess.data[0]['id']
        else:
            # Update existing conversation_sessions
            supabase.table("conversation_sessions").update({
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "summary": f"Updated: {query[:20]}..." 
            }).eq("id", session_id).execute()

        # 2. Resolve Store Location
        store = supabase.table("stores").select("fulfillment_location_id").eq("id", payload.store_id).maybe_single().execute()
        if not store or not store.data:
             return {"response": "I'm currently offline for this location.", "products": [], "session_id": session_id}
             
        fl_id = store.data['fulfillment_location_id']

        # 3. Product Search (Simple ILIKE)
        products = supabase.table("products").select("id, name, base_price").ilike("name", f"%{query}%").limit(1).execute()

        if products.data:
            product = products.data[0]
            # Find Location
            inv = supabase.table("inventory").select("aisle_number, shelf_height, quantity_on_hand, product_variants(image_url, color_name)")\
                .eq("fulfillment_location_id", fl_id)\
                .eq("product_variants.product_id", product['id'])\
                .gt("quantity_on_hand", 0)\
                .limit(1).execute()
            
            if inv and inv.data:
                rec = inv.data[0]
                variant = rec['product_variants']
                
                # Log Success (State Update - Optional)
                supabase.table("conversation_sessions").update({
                    "state": {"last_intent": "product_found", "product_id": product['id']},
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", session_id).execute()

                found_items = [{
                    "name": product['name'],
                    "variant": variant['color_name'] if variant else "Standard",
                    "price": product['base_price'],
                    "image": variant['image_url'] if variant else None,
                    "location": {
                        "aisle": rec['aisle_number'],
                        "shelf": rec['shelf_height']
                    }
                }]
                
                loc_str = f"Aisle {rec['aisle_number']}, Shelf {rec['shelf_height']}" if rec['aisle_number'] else "the main floor"
                return {
                    "response": f"I found the {product['name']} in {loc_str}.",
                    "products": found_items,
                    "session_id": session_id
                }
        
        # Log Failure (update state)
        supabase.table("conversation_sessions").update({
            "state": {"consecutive_error_count": 1},  # Store in state JSONB
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", session_id).execute()

        return {"response": "I couldn't find that item nearby.", "products": [], "session_id": session_id}

    except Exception as e:
        print(f"Chat Error: {e}")
        return {"response": "Service unavailable.", "products": [], "session_id": payload.session_id}
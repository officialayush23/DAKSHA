"""
Commerce tools.

Every tool takes (ToolContext, Args). The context carries identity (user,
web session, channel, kiosk store) and is filled in by the engine; the Args
model holds ONLY what the model may choose. There is no user_id argument
anywhere, so a prompt-injected "use user X" has nothing to bind to, and every
order/checkout lookup is scoped to tc.user_id inside the tool.

Money is never an argument either: discounts, totals and refunds are computed
by the services from server-side prices.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from app.agentic.core.registry import ToolContext, ToolResult


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _db():
    from app.core.database import SessionLocal
    return SessionLocal()


def _uid(tc: ToolContext) -> uuid.UUID:
    if not tc.user_id:
        raise PermissionError("Please sign in first.")
    return uuid.UUID(str(tc.user_id))


def _web_session(tc: ToolContext) -> Optional[uuid.UUID]:
    sid = (tc.ctx or {}).get("web_session_id")
    return uuid.UUID(sid) if sid else None


def _channel(tc: ToolContext):
    from app.enums.db_enums import ChannelEnum
    try:
        return ChannelEnum({"pwa": "app", "proactive": "web"}.get(tc.channel, tc.channel))
    except ValueError:
        return ChannelEnum.web


def _run(coro):
    """Tools run in worker threads; give async services their own loop."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _order(db, tc: ToolContext, ref: str):
    """Resolve a full id or the 8-char ref shown to the customer, scoped to them."""
    from app.models.models import Order
    uid = _uid(tc)
    ref = (ref or "").strip().lstrip("#").lower()
    if len(ref) >= 32:
        o = db.query(Order).filter(Order.id == uuid.UUID(ref), Order.user_id == uid).first()
    else:
        o = db.execute(text("""SELECT id FROM orders WHERE user_id = :u AND id::text LIKE :p
                               ORDER BY created_at DESC LIMIT 2"""), {"u": str(uid), "p": f"{ref}%"}).fetchall()
        if len(o) != 1:
            o = None
        else:
            o = db.get(Order, o[0].id)
    if not o:
        raise LookupError(f"No order #{ref[:8]} on your account.")
    return o


def _err(e: Exception) -> ToolResult:
    msg = str(e) or type(e).__name__
    return ToolResult(False, msg[:400])


def _cards(products: list) -> dict:
    return {"type": "products", "products": products}


def _hydrate(db, variant_ids: List[str], limit: int = 8, max_price=None) -> list:
    from app.models.models import GlobalInventory, ProductVariant
    from app.services.pricing_service import resolve_variant_price
    from app.services.stock import sellable
    out = []
    if not variant_ids:
        return out
    vs = {str(v.id): v for v in db.query(ProductVariant).filter(ProductVariant.id.in_(variant_ids),
                                                                 ProductVariant.active == True).all()}  # noqa: E712
    for vid in variant_ids:
        v = vs.get(str(vid))
        if not v or not v.product:
            continue
        stock = sellable(db.get(GlobalInventory, v.id))
        if stock <= 0:
            continue
        p = resolve_variant_price(db, v)
        if max_price is not None and p["final_price"] > max_price:
            continue
        out.append({"variant_id": str(v.id), "product_id": str(v.product_id), "name": v.product.name,
                    "brand": v.product.brand, "category": v.product.category, "color": v.color, "size": v.size,
                    "image": v.images[0].image_url if v.images else None, "price": p["final_price"],
                    "base_price": p["base_price"], "final_price": p["final_price"], "offer_name": p.get("offer_name"),
                    "in_stock": stock})
        if len(out) >= limit:
            break
    return out


def _brief(products: list) -> str:
    if not products:
        return "no in-stock matches"
    return "; ".join(f"{p['name']} ({p.get('color') or '-'}/{p.get('size') or '-'}) ₹{p['price']:.0f} variant_id={p['variant_id']}"
                     for p in products)


# ─────────────────────────────────────────────────────────────────────────────
# argument schemas (model-visible)
# ─────────────────────────────────────────────────────────────────────────────

class NoArgs(BaseModel):
    pass


class SearchArgs(BaseModel):
    query: str = Field(min_length=2, max_length=200, description="what the shopper is looking for")
    max_price: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, max_length=60)


class RecommendArgs(BaseModel):
    intent: Optional[str] = Field(default=None, max_length=200, description="occasion/style hint; empty = personal picks")
    max_price: Optional[float] = Field(default=None, gt=0)


class ImageArgs(BaseModel):
    image_url: str = Field(min_length=8, max_length=1000)


class VariantArgs(BaseModel):
    variant_id: uuid.UUID


class StockArgs(BaseModel):
    variant_id: uuid.UUID
    store_id: Optional[uuid.UUID] = None


class CartAddArgs(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=10)


class CartQtyArgs(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(ge=0, le=10)


class StartCheckoutArgs(BaseModel):
    fulfillment: Literal["delivery", "pickup"]
    store_id: Optional[uuid.UUID] = Field(default=None, description="required for pickup unless the shopper is at a kiosk")


class StoresArgs(BaseModel):
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)


class PlaceOrderArgs(BaseModel):
    address_id: Optional[uuid.UUID] = Field(default=None, description="for delivery")
    pickup_time: Optional[str] = Field(default=None, description="ISO time for pickup orders")
    redeem_points: int = Field(default=0, ge=0, le=100000)


class DiscountArgs(BaseModel):
    code: Optional[str] = Field(default=None, max_length=40)
    offer_id: Optional[uuid.UUID] = None


class OfferArgs(BaseModel):
    percent: Optional[float] = Field(default=None, gt=0, le=90, description="desired % off; policy may lower it")


class OrderRefArgs(BaseModel):
    order_ref: str = Field(min_length=4, max_length=40, description="order id or the short #ref")


class RescheduleArgs(BaseModel):
    order_ref: str = Field(min_length=4, max_length=40)
    new_address: Optional[str] = Field(default=None, max_length=300)


class ReturnArgs(BaseModel):
    order_ref: str = Field(min_length=4, max_length=40)
    variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=20)
    reason: str = Field(min_length=3, max_length=500)


class ExchangeArgs(BaseModel):
    order_ref: str = Field(min_length=4, max_length=40)
    old_variant_id: uuid.UUID
    new_variant_id: uuid.UUID
    reason: Literal["size", "color", "defect", "wrong_item"]


class CancelArgs(BaseModel):
    order_ref: str = Field(min_length=4, max_length=40)
    reason: str = Field(min_length=3, max_length=300)


class CancelReturnArgs(BaseModel):
    return_id: uuid.UUID


class ComplaintArgs(BaseModel):
    category: Literal["delivery", "product_quality", "payment", "refund", "staff", "app", "other"]
    description: str = Field(min_length=10, max_length=1500)
    order_ref: Optional[str] = Field(default=None, max_length=40)
    severity: Literal["low", "medium", "high", "critical"] = "medium"


class PolicyArgs(BaseModel):
    topic: Literal["returns", "exchanges", "offers", "loyalty", "cancellations", "delivery", "payments"]


class MessageArgs(BaseModel):
    purpose: Literal["post_delivery_feedback", "abandoned_cart", "wishlist_offer", "reengagement", "pickup_reminder", "order_update"]
    subject: str = Field(min_length=3, max_length=120)
    body: str = Field(min_length=10, max_length=1200)
    channels: List[Literal["in_app", "email", "telegram"]] = Field(default_factory=lambda: ["in_app"])

    @field_validator("channels")
    @classmethod
    def _non_empty(cls, v):
        return v or ["in_app"]


# ─────────────────────────────────────────────────────────────────────────────
# discovery
# ─────────────────────────────────────────────────────────────────────────────

def search_catalog(tc: ToolContext, a: SearchArgs) -> ToolResult:
    from app.services.recommendation_service import recommend
    try:
        with _db() as db:
            prods = recommend(db, str(_uid(tc)), a.query, limit=8, max_price=a.max_price, category=a.category,
                              session_id=_web_session(tc), feed_type="search")
            if not prods:   # fall back to plain semantic search without the strict threshold
                from app.services.catalog_semantic_service import semantic_catalog_search
                prods = _hydrate(db, semantic_catalog_search(db, a.query, limit=30), 8, a.max_price)
        return ToolResult(True, f"{len(prods)} results: {_brief(prods)}", {"products": prods}, _cards(prods))
    except Exception as e:
        return _err(e)


def recommend_for_me(tc: ToolContext, a: RecommendArgs) -> ToolResult:
    from app.services.recommendation_service import recommend
    try:
        with _db() as db:
            prods = recommend(db, str(_uid(tc)), a.intent, limit=8, max_price=a.max_price,
                              session_id=_web_session(tc), feed_type="home")
            if not prods:
                from app.services.trending_service import get_trending_feed
                prods = _hydrate(db, [str(p["variant_id"]) for p in get_trending_feed(db, None, limit=20)], 8, a.max_price)
        return ToolResult(True, f"{len(prods)} picks: {_brief(prods)}", {"products": prods}, _cards(prods))
    except Exception as e:
        return _err(e)


def similar_to_image(tc: ToolContext, a: ImageArgs) -> ToolResult:
    from app.services.catalog_semantic_service import search_similar_by_image
    try:
        with _db() as db:
            prods = _hydrate(db, search_similar_by_image(db, a.image_url, limit=30), 8)
        return ToolResult(True, f"{len(prods)} visually similar: {_brief(prods)}", {"products": prods}, _cards(prods))
    except Exception as e:
        return _err(e)


def trending_now(tc: ToolContext, a: NoArgs) -> ToolResult:
    from app.services.trending_service import get_trending_feed
    try:
        with _db() as db:
            prods = _hydrate(db, [str(p["variant_id"]) for p in get_trending_feed(db, None, limit=24)], 8)
        return ToolResult(True, f"trending: {_brief(prods)}", {"products": prods}, _cards(prods))
    except Exception as e:
        return _err(e)


def product_details(tc: ToolContext, a: VariantArgs) -> ToolResult:
    from app.models.models import GlobalInventory, ProductVariant
    from app.services.pricing_service import resolve_variant_price
    from app.services.stock import sellable
    try:
        with _db() as db:
            v = db.get(ProductVariant, a.variant_id)
            if not v or not v.product:
                return ToolResult(False, "No such product.")
            p = v.product
            siblings = []
            for s in p.variants if hasattr(p, "variants") else []:
                if not s.active:
                    continue
                siblings.append({"variant_id": str(s.id), "color": s.color, "size": s.size,
                                 "in_stock": sellable(db.get(GlobalInventory, s.id)),
                                 "price": resolve_variant_price(db, s)["final_price"]})
            stats = db.execute(text("SELECT avg_rating, review_count FROM product_review_stats WHERE product_id = :p"),
                               {"p": str(p.id)}).first()
            data = {"name": p.name, "brand": p.brand, "category": p.category, "fabric": p.fabric_type,
                    "occasion": p.occasion, "description": (p.description or "")[:400],
                    "rating": float(stats.avg_rating) if stats and stats.avg_rating else None,
                    "reviews": stats.review_count if stats else 0, "variants": siblings[:20]}
            msg = (f"{p.name} by {p.brand}: {data['description'][:160]} | rating {data['rating']} | variants: "
                   + "; ".join(f"{s['color']}/{s['size']} ₹{s['price']:.0f} stock {s['in_stock']} id={s['variant_id']}" for s in siblings[:10]))
            return ToolResult(True, msg, data, _cards(_hydrate(db, [str(v.id)], 1)))
    except Exception as e:
        return _err(e)


def check_stock(tc: ToolContext, a: StockArgs) -> ToolResult:
    from app.models.models import GlobalInventory, StoreInventory
    from app.services.stock import store_available, warehouse_available
    try:
        with _db() as db:
            inv = db.get(GlobalInventory, a.variant_id)
            data = {"warehouse": warehouse_available(inv)}
            sid = a.store_id or (uuid.UUID(tc.store_id) if tc.store_id else None)
            if sid:
                si = db.query(StoreInventory).filter_by(store_id=sid, product_variant_id=a.variant_id).first()
                data["store"] = store_available(si)
        return ToolResult(True, f"stock: {data}", data)
    except Exception as e:
        return _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# cart
# ─────────────────────────────────────────────────────────────────────────────

def _cart_result(db, uid, msg) -> ToolResult:
    from app.services.cart_service import get_hydrated_cart
    cart = get_hydrated_cart(db, uid)
    lines = "; ".join(f"{i['name']} {i['color']}/{i['size']} x{i['quantity']} ₹{i['line_total']:.0f} (variant_id={i['variant_id']})"
                      for i in cart["items"]) or "empty"
    return ToolResult(True, f"{msg} Cart now: {lines}. Total ₹{cart['grand_total']:.0f}.",
                      {"cart": cart}, {"type": "cart", **json.loads(json.dumps(cart, default=str))})


def view_cart(tc: ToolContext, a: NoArgs) -> ToolResult:
    try:
        with _db() as db:
            return _cart_result(db, _uid(tc), "")
    except Exception as e:
        return _err(e)


def add_to_cart(tc: ToolContext, a: CartAddArgs) -> ToolResult:
    from app.services.cart_service import add_item_to_cart
    try:
        with _db() as db:
            uid = _uid(tc)
            add_item_to_cart(db=db, user_id=uid, session_id=_web_session(tc), product_variant_id=a.variant_id,
                             quantity=a.quantity, channel=_channel(tc), source="agent_action")
            return _cart_result(db, uid, f"Added {a.quantity}.")
    except Exception as e:
        return _err(e)


def update_cart_item(tc: ToolContext, a: CartQtyArgs) -> ToolResult:
    from app.services.cart_service import update_cart_item_quantity
    try:
        with _db() as db:
            uid = _uid(tc)
            update_cart_item_quantity(db=db, user_id=uid, session_id=_web_session(tc), product_variant_id=a.variant_id,
                                      new_quantity=a.quantity, channel=_channel(tc), source="agent_action")
            return _cart_result(db, uid, f"Quantity set to {a.quantity}.")
    except Exception as e:
        return _err(e)


def remove_from_cart(tc: ToolContext, a: VariantArgs) -> ToolResult:
    from app.services.cart_service import remove_item_from_cart
    try:
        with _db() as db:
            uid = _uid(tc)
            ok = remove_item_from_cart(db=db, user_id=uid, session_id=_web_session(tc), product_variant_id=a.variant_id,
                                       channel=_channel(tc), source="agent_action")
            if not ok:
                return ToolResult(False, "That item isn't in the cart.")
            return _cart_result(db, uid, "Removed.")
    except Exception as e:
        return _err(e)


def add_to_wishlist(tc: ToolContext, a: VariantArgs) -> ToolResult:
    from app.services.wishlist_service import add_to_wishlist as _add
    try:
        with _db() as db:
            _add(db, user_id=_uid(tc), product_variant_id=a.variant_id, channel=_channel(tc), session_id=_web_session(tc))
        return ToolResult(True, "Saved to wishlist.")
    except Exception as e:
        return _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# checkout
# ─────────────────────────────────────────────────────────────────────────────

def list_addresses(tc: ToolContext, a: NoArgs) -> ToolResult:
    try:
        with _db() as db:
            rows = db.execute(text("""SELECT id, label, address_line1, city, pincode, is_default FROM user_addresses
                                      WHERE user_id = :u ORDER BY is_default DESC"""), {"u": str(_uid(tc))}).fetchall()
        addrs = [{"address_id": str(r.id), "label": r.label, "line": r.address_line1, "city": r.city,
                  "pincode": r.pincode, "default": r.is_default} for r in rows]
        if not addrs:
            return ToolResult(True, "No saved addresses. Ask the customer to add one in their profile.", {"addresses": []})
        return ToolResult(True, "; ".join(f"{x['label']}: {x['line']}, {x['city']} (address_id={x['address_id']})" for x in addrs),
                          {"addresses": addrs}, {"type": "addresses", "addresses": addrs})
    except Exception as e:
        return _err(e)


def find_pickup_stores(tc: ToolContext, a: StoresArgs) -> ToolResult:
    from app.services.cart_service import get_active_cart
    from app.services.store_availability_service import get_nearest_stores_with_cart
    try:
        with _db() as db:
            uid = _uid(tc)
            cart = get_active_cart(db, user_id=uid)
            if not cart or not cart.items:
                return ToolResult(False, "The cart is empty.")
            lat, lng = a.lat, a.lng
            if lat is None or lng is None:
                if tc.store_id:
                    r = db.execute(text("SELECT ST_Y(location::geometry) lat, ST_X(location::geometry) lng FROM stores WHERE id=:s"),
                                   {"s": tc.store_id}).first()
                else:
                    r = db.execute(text("""SELECT latitude lat, longitude lng FROM user_addresses
                                           WHERE user_id = :u AND latitude IS NOT NULL ORDER BY is_default DESC LIMIT 1"""),
                                   {"u": str(uid)}).first()
                if not r:
                    return ToolResult(False, "I need the shopper's location (or a saved address with a pin) to find stores.")
                lat, lng = r.lat, r.lng
            stores = get_nearest_stores_with_cart(db, cart.id, lat, lng)
        if not stores:
            return ToolResult(True, "No store within 20 km has every cart item. Suggest delivery instead.", {"stores": []})
        return ToolResult(True, "; ".join(f"{s['name']} {s['distance_km']} km (store_id={s['store_id']})" for s in stores),
                          {"stores": stores}, {"type": "stores", "stores": stores})
    except Exception as e:
        return _err(e)


def start_checkout(tc: ToolContext, a: StartCheckoutArgs) -> ToolResult:
    from app.enums.db_enums import FulfillmentTypeEnum
    from app.services.cart_service import get_active_cart
    from app.services.checkout_service import create_checkout_after_fulfillment
    try:
        with _db() as db:
            uid = _uid(tc)
            cart = get_active_cart(db, user_id=uid)
            if not cart or not cart.items:
                return ToolResult(False, "The cart is empty.")
            store = a.store_id or (uuid.UUID(tc.store_id) if (a.fulfillment == "pickup" and tc.store_id) else None)
            if a.fulfillment == "pickup" and not store:
                return ToolResult(False, "Pickup needs a store: call find_pickup_stores first.")
            co = create_checkout_after_fulfillment(
                db=db, user_id=uid, session_id=_web_session(tc), cart_id=cart.id,
                fulfillment_type=FulfillmentTypeEnum(a.fulfillment), store_id=store, channel=_channel(tc))
            data = {"checkout_id": str(co.id), "locked_price": float(co.locked_price), "fulfillment": a.fulfillment,
                    "hold_minutes": 12}
        return ToolResult(True, f"Checkout open, stock held for 12 min, locked price ₹{data['locked_price']:.0f}.",
                          data, {"type": "checkout", **data})
    except Exception as e:
        return _err(e)


def _open_checkout(db, uid):
    from app.models.models import CheckoutSession
    co = (db.query(CheckoutSession).filter(CheckoutSession.user_id == uid)
          .order_by(CheckoutSession.updated_at.desc()).first())
    if not co or getattr(co.state, "value", co.state) in ("ORDER_CONFIRMED", "CANCELLED", "ROLLED_BACK"):
        raise LookupError("There's no open checkout. Start one first.")
    return co


def place_order(tc: ToolContext, a: PlaceOrderArgs) -> ToolResult:
    from app.services.checkout_service import finalize_checkout
    try:
        with _db() as db:
            uid = _uid(tc)
            co = _open_checkout(db, uid)
            when = None
            if a.pickup_time:
                when = datetime.fromisoformat(a.pickup_time.replace("Z", "+00:00"))
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
            elif getattr(co.fulfillment_type, "value", co.fulfillment_type) == "pickup":
                when = datetime.now(timezone.utc) + timedelta(hours=2)
            res = _run(finalize_checkout(db=db, checkout_id=co.id, delivery_address_id=a.address_id,
                                         scheduled_time=when, redeem_loyalty_points=a.redeem_points, user_id=uid))
        if res.get("status") == "payment_failed":
            return ToolResult(False, f"Payment failed: {res.get('reason')}", res)
        if res.get("status") == "already_completed":
            return ToolResult(True, "This checkout was already completed.", res)
        oid = str(res.get("order_id"))
        return ToolResult(True, f"Order #{oid[:8]} placed.", {"order_id": oid},
                          {"type": "order", "order_id": oid, "ref": oid[:8], "status": "confirmed"})
    except Exception as e:
        return _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# offers & loyalty
# ─────────────────────────────────────────────────────────────────────────────

def my_offers(tc: ToolContext, a: NoArgs) -> ToolResult:
    from app.services.coupon_service import get_eligible_coupons
    try:
        with _db() as db:
            uid = _uid(tc)
            from app.services.cart_service import get_hydrated_cart
            cart = get_hydrated_cart(db, uid)
            try:
                co = _open_checkout(db, uid)
                total = float(co.locked_price or 0)
            except LookupError:
                total = cart["grand_total"]
            cats = set()
            if cart["items"]:
                rows = db.execute(text("""SELECT DISTINCT p.category, p.brand FROM product_variants pv JOIN products p ON p.id = pv.product_id
                                          WHERE pv.id = ANY(:ids)"""), {"ids": [i["variant_id"] for i in cart["items"]]}).fetchall()
                for r in rows:
                    cats |= {x for x in (r.category, r.brand) if x}
            res = get_eligible_coupons(db, uid, total, cats)
        msg = ("personal: " + "; ".join(f"{o['offer_name']} (offer_id={o['id']})" for o in res["personalized"])
               + " | coupons: " + "; ".join(f"{c['code']} {c.get('description') or ''}" for c in res["system"][:8]))
        return ToolResult(True, msg, res, {"type": "offers", **res})
    except Exception as e:
        return _err(e)


def apply_discount(tc: ToolContext, a: DiscountArgs) -> ToolResult:
    from app.services.coupon_service import apply_coupon
    try:
        with _db() as db:
            uid = _uid(tc)
            co = _open_checkout(db, uid)
            d = apply_coupon(db, co.id, coupon_code=a.code, personal_offer_id=a.offer_id, user_id=uid)
            total = float(co.locked_price or 0) - d
        return ToolResult(True, f"Discount ₹{d:.0f} applied; new total ₹{total:.0f}.",
                          {"discount": d, "total": total}, {"type": "checkout", "checkout_id": str(co.id),
                                                            "locked_price": float(co.locked_price), "discount": d, "total": total})
    except Exception as e:
        return _err(e)


def create_personal_offer(tc: ToolContext, a: OfferArgs) -> ToolResult:
    from app.services.personalized_offer_service import generate_dynamic_offer
    try:
        with _db() as db:
            o = generate_dynamic_offer(db, _uid(tc), requested_pct=a.percent)
            data = {"offer_id": str(o.id), "name": o.offer_name, "value": float(o.discount_value),
                    "expires_at": o.expires_at.isoformat()}
        return ToolResult(True, f"Offer ready: {data['name']} (offer_id={data['offer_id']}), expires {data['expires_at'][:16]}.",
                          data, {"type": "offers", "personalized": [data], "system": []})
    except Exception as e:
        return _err(e)


def loyalty_status(tc: ToolContext, a: NoArgs) -> ToolResult:
    from app.services.loyalty_service import get_balance
    from app.ai.policy.company_policy import LOYALTY_POLICY
    try:
        with _db() as db:
            pts = int(get_balance(db, _uid(tc)))
        worth = pts / 100 * LOYALTY_POLICY.rupees_per_100_points
        return ToolResult(True, f"{pts} points (worth about ₹{worth:.0f}); redeemable on carts ≥ ₹{LOYALTY_POLICY.min_cart_for_redemption:.0f}, "
                                f"max {int(LOYALTY_POLICY.max_redemption_pct_of_cart*100)}% of the cart.", {"points": pts})
    except Exception as e:
        return _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# orders, fulfilment, post-purchase
# ─────────────────────────────────────────────────────────────────────────────

def my_orders(tc: ToolContext, a: NoArgs) -> ToolResult:
    try:
        with _db() as db:
            rows = db.execute(text("""SELECT id, order_status, total_amount, created_at, fulfillment_type FROM orders
                                      WHERE user_id = :u ORDER BY created_at DESC LIMIT 10"""), {"u": str(_uid(tc))}).fetchall()
        orders = [{"ref": str(r.id)[:8], "order_id": str(r.id), "status": r.order_status, "total": float(r.total_amount or 0),
                   "placed": r.created_at.isoformat()[:10], "fulfillment": r.fulfillment_type} for r in rows]
        return ToolResult(True, "; ".join(f"#{o['ref']} {o['status']} ₹{o['total']:.0f} {o['placed']}" for o in orders) or "no orders",
                          {"orders": orders}, {"type": "orders", "orders": orders})
    except Exception as e:
        return _err(e)


def order_details(tc: ToolContext, a: OrderRefArgs) -> ToolResult:
    try:
        with _db() as db:
            o = _order(db, tc, a.order_ref)
            items = db.execute(text("""SELECT oi.product_variant_id, oi.quantity, oi.price_at_purchase, p.name, pv.color, pv.size
                                       FROM order_items oi JOIN product_variants pv ON pv.id = oi.product_variant_id
                                       JOIN products p ON p.id = pv.product_id WHERE oi.order_id = :o"""), {"o": str(o.id)}).fetchall()
            hist = db.execute(text("""SELECT status, description, updated_at FROM order_status_history
                                      WHERE order_id = :o ORDER BY updated_at"""), {"o": str(o.id)}).fetchall()
            ship = db.execute(text("SELECT carrier, tracking_number, status, estimated_delivery FROM shipments WHERE order_id = :o"),
                              {"o": str(o.id)}).first()
            track = db.execute(text("""SELECT status, location_text, carrier_message, recorded_at FROM delivery_tracking
                                       WHERE order_id = :o ORDER BY recorded_at DESC LIMIT 3"""), {"o": str(o.id)}).fetchall()
        data = {"ref": str(o.id)[:8], "order_id": str(o.id), "status": getattr(o.order_status, "value", o.order_status),
                "total": float(o.total_amount or 0), "fulfillment": getattr(o.fulfillment_type, "value", o.fulfillment_type),
                "items": [{"variant_id": str(i.product_variant_id), "name": i.name, "color": i.color, "size": i.size,
                           "qty": i.quantity, "price": float(i.price_at_purchase)} for i in items],
                "history": [{"status": h.status, "note": h.description, "at": h.updated_at.isoformat() if h.updated_at else None} for h in hist],
                "shipment": dict(ship._mapping) if ship else None,
                "tracking": [dict(t._mapping) for t in track]}
        msg = (f"#{data['ref']} {data['status']} ₹{data['total']:.0f}; items: "
               + "; ".join(f"{i['name']} {i['color']}/{i['size']} x{i['qty']} (variant_id={i['variant_id']})" for i in data["items"])
               + (f"; shipment {ship.status} via {ship.carrier}, ETA {ship.estimated_delivery}" if ship else "")
               + (f"; latest scan: {track[0].status} {track[0].location_text or ''}" if track else ""))
        return ToolResult(True, msg, json.loads(json.dumps(data, default=str)), {"type": "order", **json.loads(json.dumps(data, default=str))})
    except Exception as e:
        return _err(e)


def reschedule_delivery(tc: ToolContext, a: RescheduleArgs) -> ToolResult:
    from app.services.fulfillment_agent_service import reschedule_delivery as _rs
    try:
        with _db() as db:
            o = _order(db, tc, a.order_ref)
            res = _run(_rs(db, o.id, a.new_address))
        return ToolResult(True, f"Delivery for #{str(o.id)[:8]} rescheduled.", res)
    except Exception as e:
        return _err(e)


def request_return(tc: ToolContext, a: ReturnArgs) -> ToolResult:
    from app.schemas.schemas import ReturnRequest
    from app.services.support_service import request_return as _req
    try:
        with _db() as db:
            o = _order(db, tc, a.order_ref)
            r = _req(db, _uid(tc), ReturnRequest(order_id=o.id, product_variant_id=a.variant_id, quantity=a.quantity, reason=a.reason))
        return ToolResult(True, f"Return requested (id {str(r.id)[:8]}). Pickup will be arranged after approval.",
                          {"return_id": str(r.id)}, {"type": "return", "return_id": str(r.id), "status": "requested"})
    except Exception as e:
        return _err(e)


def request_exchange(tc: ToolContext, a: ExchangeArgs) -> ToolResult:
    from app.schemas.schemas import ExchangeRequest
    from app.services.support_service import request_exchange as _req
    try:
        with _db() as db:
            o = _order(db, tc, a.order_ref)
            x = _req(db, _uid(tc), ExchangeRequest(order_id=o.id, old_variant_id=a.old_variant_id,
                                                    new_variant_id=a.new_variant_id))
        return ToolResult(True, f"Exchange requested (id {str(x.id)[:8]}).", {"exchange_id": str(x.id)})
    except Exception as e:
        return _err(e)


def cancel_order(tc: ToolContext, a: CancelArgs) -> ToolResult:
    from app.services.support_service import request_order_cancellation
    try:
        with _db() as db:
            o = _order(db, tc, a.order_ref)
            req = request_order_cancellation(db, _uid(tc), o.id, a.reason)
            note = (req.change_payload or {}).get("policy_note", "")
        return ToolResult(True, f"Cancellation requested for #{str(o.id)[:8]}. {note}", {"request_id": str(req.id)})
    except Exception as e:
        return _err(e)


def my_returns(tc: ToolContext, a: NoArgs) -> ToolResult:
    from app.services.support_service import get_user_exchanges, get_user_returns
    try:
        with _db() as db:
            uid = _uid(tc)
            rs = [{"return_id": str(r.id), "order": str(r.order_id)[:8], "status": r.status.value, "reason": r.reason}
                  for r in get_user_returns(db, uid)]
            xs = [{"exchange_id": str(x.id), "order": str(x.order_id)[:8], "status": x.status.value}
                  for x in get_user_exchanges(db, uid)]
        return ToolResult(True, f"returns: {rs[:5]} exchanges: {xs[:5]}", {"returns": rs, "exchanges": xs})
    except Exception as e:
        return _err(e)


def cancel_return(tc: ToolContext, a: CancelReturnArgs) -> ToolResult:
    from app.services.support_service import cancel_return as _cr
    try:
        with _db() as db:
            r = _run(_cr(db, a.return_id, _uid(tc), "Customer cancelled via assistant"))
        return ToolResult(True, f"Return {str(r.id)[:8]} cancelled.")
    except Exception as e:
        return _err(e)


def file_complaint(tc: ToolContext, a: ComplaintArgs) -> ToolResult:
    from app.schemas.schemas import ComplaintCreate
    from app.services.support_service import file_complaint as _fc
    try:
        with _db() as db:
            uid = _uid(tc)
            oid = _order(db, tc, a.order_ref).id if a.order_ref else None
            c = _fc(db, uid, ComplaintCreate(user_id=uid, order_id=oid, session_id=_web_session(tc), category=a.category,
                                             description=f"[{a.severity}] {a.description}"))
        return ToolResult(True, f"Complaint logged (ticket {str(c.id)[:8]}).", {"complaint_id": str(c.id), "severity": a.severity})
    except Exception as e:
        return _err(e)


def store_policy(tc: ToolContext, a: PolicyArgs) -> ToolResult:
    from app.ai.policy.company_policy import POLICY_CONTEXT
    block, keep = [], False
    head = {"returns": "RETURNS", "exchanges": "EXCHANGES", "offers": "OFFERS", "loyalty": "LOYALTY",
            "cancellations": "CANCELLATIONS", "delivery": "DELIVERY", "payments": "PAYMENTS"}[a.topic]
    for line in POLICY_CONTEXT.splitlines():
        if line.strip().startswith(head):
            keep = True
            continue
        if keep and line.strip() and line.strip().isupper():
            break
        if keep and line.strip():
            block.append(line.strip("• ").strip())
    return ToolResult(True, " ".join(block) or "No policy text found.", {"policy": block})


def my_profile(tc: ToolContext, a: NoArgs) -> ToolResult:
    from app.services.user_services import get_hydrated_user_profile
    try:
        with _db() as db:
            prof = get_hydrated_user_profile(db, _uid(tc))
        prof = json.loads(json.dumps(prof, default=str))
        return ToolResult(True, json.dumps(prof)[:900], prof)
    except Exception as e:
        return _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# engagement (proactive)
# ─────────────────────────────────────────────────────────────────────────────

def send_customer_message(tc: ToolContext, a: MessageArgs) -> ToolResult:
    from app.services.notification_service import notify_user
    try:
        with _db() as db:
            _run(notify_user(db=db, user_id=_uid(tc), subject=a.subject, message=a.body, message_type=a.purpose,
                             send_email="email" in a.channels, send_telegram="telegram" in a.channels,
                             send_in_app="in_app" in a.channels))
        return ToolResult(True, f"Sent '{a.subject}' via {', '.join(a.channels)}.", {"channels": a.channels})
    except Exception as e:
        return _err(e)

"""
The commerce domain pack: DAKSHA's shop expressed as agents + tools + policies.

Swap this file for another pack (clinic, campus, bank ...) and the same graph
runs a different business.
"""
from __future__ import annotations

import uuid

from sqlalchemy import text

from app.agentic.commerce import policies as P
from app.agentic.commerce import tools as T
from app.agentic.commerce.context import load_context, render_context
from app.agentic.core.registry import AgentSpec, DomainPack, ToolContext, ToolResult, ToolSpec


def _tool(fn, args, desc, effect="read", policy=None) -> ToolSpec:
    return ToolSpec(fn.__name__, desc, args, fn, effect, policy)


TOOLS = {t.name: t for t in [
    # discovery
    _tool(T.search_catalog, T.SearchArgs, "Semantic product search with optional max price/category. Returns in-stock variants."),
    _tool(T.recommend_for_me, T.RecommendArgs, "Personalised picks from taste profile, collaborative signals and trends."),
    _tool(T.similar_to_image, T.ImageArgs, "Find products visually similar to an uploaded image URL."),
    _tool(T.trending_now, T.NoArgs, "Currently trending in-stock products."),
    _tool(T.product_details, T.VariantArgs, "Details, rating and all colour/size variants with stock for one product."),
    _tool(T.check_stock, T.StockArgs, "Warehouse and (optional) store stock for a variant."),
    _tool(T.add_to_wishlist, T.VariantArgs, "Save a variant to the wishlist.", "write"),
    # cart
    _tool(T.view_cart, T.NoArgs, "Show the unified cart (same on web, app and kiosk)."),
    _tool(T.add_to_cart, T.CartAddArgs, "Add a variant to the cart (use the exact variant_id from results).", "write"),
    _tool(T.update_cart_item, T.CartQtyArgs, "Set a cart line quantity (0 removes it).", "write"),
    _tool(T.remove_from_cart, T.VariantArgs, "Remove a variant from the cart.", "write"),
    # checkout
    _tool(T.list_addresses, T.NoArgs, "Saved delivery addresses with address_id."),
    _tool(T.find_pickup_stores, T.StoresArgs, "Nearest stores that have the whole cart in stock."),
    _tool(T.start_checkout, T.StartCheckoutArgs, "Lock price and hold stock for 12 minutes (delivery or pickup).", "write", P.no_proactive),
    _tool(T.place_order, T.PlaceOrderArgs, "Pay and place the order for the open checkout. The customer must confirm.", "sensitive", P.place_order_policy),
    # offers & loyalty
    _tool(T.my_offers, T.NoArgs, "Personal offers and coupons valid for the current cart/checkout."),
    _tool(T.apply_discount, T.DiscountArgs, "Apply a coupon code or a personal offer to the open checkout (server computes the amount).", "write"),
    _tool(T.create_personal_offer, T.OfferArgs, "Create a personal offer; capped by the customer's tier.", "write", P.offer_policy),
    _tool(T.loyalty_status, T.NoArgs, "Loyalty points balance and redemption rules."),
    # fulfilment & post-purchase
    _tool(T.my_orders, T.NoArgs, "Recent orders with short refs."),
    _tool(T.order_details, T.OrderRefArgs, "Items, status history, shipment and tracking for one order."),
    _tool(T.reschedule_delivery, T.RescheduleArgs, "Reschedule a failed delivery, optionally to a new address.", "write"),
    _tool(T.request_return, T.ReturnArgs, "Request a return for a delivered item.", "write", P.return_policy),
    _tool(T.request_exchange, T.ExchangeArgs, "Request an exchange for a delivered item.", "write"),
    _tool(T.cancel_order, T.CancelArgs, "Request cancellation of an order (fees may apply after packing).", "write", P.cancel_policy),
    _tool(T.my_returns, T.NoArgs, "Open and past returns/exchanges."),
    _tool(T.cancel_return, T.CancelReturnArgs, "Withdraw a pending return request.", "write"),
    # support
    _tool(T.file_complaint, T.ComplaintArgs, "Log a complaint ticket.", "write", P.complaint_policy),
    _tool(T.store_policy, T.PolicyArgs, "Official policy text for a topic (returns, offers, delivery ...)."),
    _tool(T.my_profile, T.NoArgs, "Customer profile and preferences."),
    # engagement
    _tool(T.send_customer_message, T.MessageArgs, "Send a message to the customer (in-app/email/telegram).", "sensitive", P.message_policy),
]}

AGENTS = [
    AgentSpec("discovery", "Discovery Agent",
              "finding products: search, personal picks, image search, trending, product details, stock, wishlist",
              "Find products that fit the request. Prefer search_catalog for explicit needs and recommend_for_me for "
              "open-ended ones. Respect budget and size if mentioned. Return a short list; the app shows the cards.",
              ["search_catalog", "recommend_for_me", "similar_to_image", "trending_now", "product_details", "check_stock",
               "add_to_wishlist"]),
    AgentSpec("cart", "Cart Agent", "adding, removing, changing quantities and showing the cart",
              "Change the cart exactly as asked. Use the variant_id from earlier results or the cart in context; if the "
              "shopper refers to 'the blue one', match it to a listed variant. Never guess an id.",
              ["view_cart", "add_to_cart", "update_cart_item", "remove_from_cart", "product_details"]),
    AgentSpec("checkout", "Checkout Agent", "starting checkout, choosing delivery/pickup, addresses, stores, placing the order",
              "Move the cart to a placed order. Start checkout (delivery or pickup), get the address or store, then call "
              "place_order; the system will ask the customer to confirm the amount. Never place an order the customer "
              "did not ask for.",
              ["view_cart", "list_addresses", "find_pickup_stores", "start_checkout", "apply_discount", "place_order"],
              max_actions=5),
    AgentSpec("offers", "Offers & Loyalty Agent", "coupons, personal offers, loyalty points, applying discounts",
              "Find the best valid saving. Check my_offers, apply the best one to an open checkout, and explain points. "
              "Never promise a discount the tools did not return.",
              ["my_offers", "apply_discount", "create_personal_offer", "loyalty_status"]),
    AgentSpec("fulfillment", "Fulfilment Agent", "order status, tracking, delivery issues, rescheduling, pickup stores",
              "Answer where an order is and fix delivery problems.",
              ["my_orders", "order_details", "reschedule_delivery", "find_pickup_stores", "check_stock"]),
    AgentSpec("post_purchase", "Post-Purchase Agent", "returns, exchanges, cancellations",
              "Handle returns, exchanges and cancellations within policy. Look up the order first, confirm the item, "
              "then file the request. If policy blocks it, say why and offer the alternative (e.g. exchange or complaint).",
              ["my_orders", "order_details", "request_return", "request_exchange", "cancel_order", "my_returns",
               "cancel_return", "store_policy"], max_actions=5),
    AgentSpec("support", "Support Agent", "complaints, policies, account questions",
              "Resolve account and policy questions and log complaints with the right category and severity.",
              ["file_complaint", "store_policy", "my_profile", "my_orders", "order_details"]),
    AgentSpec("engagement", "Engagement Agent", "proactive follow-ups: feedback requests, abandoned carts, wishlist nudges",
              "Write short, personal, non-pushy messages grounded in the trigger data. One message per run. Offer a "
              "personal discount only for abandoned carts or long-waiting wishlist items.",
              ["send_customer_message", "create_personal_offer", "my_orders", "view_cart"]),
]


def handoff(tc: ToolContext, reason: str, summary: str) -> ToolResult:
    from app.core.database import SessionLocal
    try:
        with SessionLocal() as db:
            existing = db.execute(text("""SELECT id FROM agent_handoffs WHERE chat_session_id = :s
                                          AND status IN ('open','in_progress') LIMIT 1"""), {"s": tc.session_id}).first()
            if existing:
                return ToolResult(True, "already with a human", {"handoff_id": str(existing.id)})
            hid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO agent_handoffs (id, user_id, chat_session_id, from_agent_name, reason, summary, status, escalation_level, created_at)
                VALUES (:id, :u, :s, 'Orchestrator', :r, :sum, 'open', 1, now())
            """), {"id": hid, "u": tc.user_id, "s": tc.session_id, "r": reason[:250], "sum": summary[:4000]})
            db.commit()
        try:
            from app.api.routers.websocket_handoff import notify_admins_new_handoff
            notify_admins_new_handoff(hid)
        except Exception:
            pass
        return ToolResult(True, "handoff opened", {"handoff_id": hid})
    except Exception as e:
        return ToolResult(False, str(e)[:300])


def build_pack() -> DomainPack:
    from app.ai.policy.company_policy import HANDOFF_POLICY
    return DomainPack(
        name="commerce",
        persona=("You are Daksha, the shopping concierge of a fashion store that sells online, in its app and at "
                 "in-store kiosks. You are warm, brief and exact. Prices, stock and order facts come only from tools."),
        agents=AGENTS,
        tools=TOOLS,
        load_context=load_context,
        render_context=render_context,
        handoff=handoff,
        handoff_phrases=list(HANDOFF_POLICY.trigger_keywords) + ["talk to human", "customer care", "real human", "speak to someone"],
        injection_markers=["ignore previous", "ignore all previous", "system prompt", "you are now", "developer mode",
                           "act as admin", "set the price", "change the price", "user_id", "override policy"],
        max_failures_before_handoff=HANDOFF_POLICY.max_agent_failures_before_handoff,
        max_plan_steps=4,
        max_total_actions=10,
    )

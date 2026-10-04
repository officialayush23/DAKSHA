"""
Proactive automation.

A scanner finds moments worth acting on and hands each one to the SAME graph
in "proactive" mode. The engagement agent drafts the message; the policy gate
lets transactional messages through and queues marketing ones (abandoned
carts, wishlist nudges, re-engagement) for staff approval. Every trigger has a
de-duplication key, so a restart or a second worker never double-sends.

Deterministic housekeeping (releasing expired stock holds) runs here too, but
without the model.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import text

log = logging.getLogger("daksha.proactive")
MAX_TRIGGERS_PER_SCAN = 15


def _db():
    from app.core.database import SessionLocal
    return SessionLocal()


def release_expired_holds() -> int:
    from app.services.inventory_reservation_service import release_reservations
    n = 0
    with _db() as db:
        rows = db.execute(text("""
            SELECT id FROM checkout_sessions
            WHERE inventory_locked = TRUE AND reserved_until < now() AND state <> 'ORDER_CONFIRMED'
        """)).fetchall()
        for r in rows:
            release_reservations(db, r.id)
            db.execute(text("UPDATE checkout_sessions SET inventory_locked = FALSE, state = 'ROLLED_BACK' WHERE id = :i"), {"i": r.id})
            n += 1
        db.commit()
    return n


def compute_trending(days: int = 30, top: int = 50) -> int:
    """Rebuild trending_products from the last `days` of purchases, carts and views.
    Nothing filled this table before, so 'trending' always came back empty."""
    now = datetime.now(timezone.utc)
    with _db() as db:
        rows = db.execute(text("""
            WITH sig AS (
                SELECT oi.product_variant_id AS v, 3.0 * oi.quantity AS w
                  FROM order_items oi JOIN orders o ON o.id = oi.order_id WHERE o.created_at > :since
                UNION ALL
                SELECT (e.event_metadata->>'variant_id')::uuid, 1.0 FROM events e
                 WHERE e.event_type = 'add_to_cart' AND e.created_at > :since AND e.event_metadata ? 'variant_id'
                UNION ALL
                SELECT e.entity_id, 0.2 FROM events e
                 WHERE e.event_type = 'product_view' AND e.entity_type = 'product_variant' AND e.created_at > :since
            )
            SELECT sig.v, sum(sig.w) AS score FROM sig
            JOIN product_variants pv ON pv.id = sig.v AND pv.active
            JOIN global_inventory gi ON gi.product_variant_id = sig.v AND gi.reserved_stock + gi.assigned_stock > 0
            GROUP BY sig.v ORDER BY score DESC LIMIT :top
        """), {"since": now - timedelta(days=days), "top": top}).fetchall()
        if not rows:   # cold start: newest in-stock variants
            rows = db.execute(text("""SELECT pv.id AS v, 0.01 AS score FROM product_variants pv
                                      JOIN global_inventory gi ON gi.product_variant_id = pv.id
                                      WHERE pv.active AND gi.reserved_stock + gi.assigned_stock > 0
                                      ORDER BY pv.created_at DESC LIMIT :top"""), {"top": top}).fetchall()
        db.execute(text("DELETE FROM trending_products WHERE scope = 'all'"))
        for i, r in enumerate(rows, 1):
            db.execute(text("""INSERT INTO trending_products (scope, scope_value, product_variant_id, rank_position,
                               trending_score, year, month, computed_at)
                               VALUES ('all', 'all', :v, :rank, :s, :y, :m, now())"""),
                       {"v": r.v, "rank": i, "s": float(r.score), "y": now.year, "m": now.month})
        db.commit()
    return len(rows)


def find_triggers(now: datetime | None = None) -> List[Dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    out: List[Dict[str, Any]] = []
    with _db() as db:
        # 1. delivered 1-3 days ago and no feedback request yet
        for r in db.execute(text("""
            SELECT o.id, o.user_id, o.total_amount FROM orders o
            WHERE o.order_status = 'delivered' AND o.feedback_requested = FALSE
              AND o.created_at < :old LIMIT 10
        """), {"old": now - timedelta(days=1)}).fetchall():
            out.append({"type": "post_delivery_feedback", "user_id": str(r.user_id), "key": str(r.id),
                        "goal": "Thank the customer and ask how the order was; invite a review. Do not offer discounts.",
                        "data": {"order_ref": str(r.id)[:8], "total": float(r.total_amount or 0)}})
        # 2. carts idle 6h-72h with items and no newer order
        for r in db.execute(text("""
            SELECT c.id, c.user_id, c.updated_at, count(ci.*) AS n FROM carts c JOIN cart_items ci ON ci.cart_id = c.id
            WHERE c.user_id IS NOT NULL AND c.updated_at BETWEEN :a AND :b
              AND NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = c.user_id AND o.created_at > c.updated_at)
            GROUP BY c.id LIMIT 10
        """), {"a": now - timedelta(hours=72), "b": now - timedelta(hours=6)}).fetchall():
            out.append({"type": "abandoned_cart", "user_id": str(r.user_id),
                        "key": f"{r.id}:{r.updated_at.isoformat()[:13]}",
                        "goal": "Remind the customer about the items left in their cart. You may create one personal offer.",
                        "data": {"items": r.n}})
        # 3. wishlist items waiting 7+ days
        for r in db.execute(text("""
            SELECT w.user_id, min(w.added_at) AS since, count(*) AS n FROM user_wishlist w
            WHERE w.added_at < :old GROUP BY w.user_id LIMIT 10
        """), {"old": now - timedelta(days=7)}).fetchall():
            out.append({"type": "wishlist_offer", "user_id": str(r.user_id), "key": f"{r.user_id}:{now.isoformat()[:7]}",
                        "goal": "Nudge the customer about wishlist items they saved a while ago; a tier-capped offer is allowed.",
                        "data": {"items": r.n, "since": r.since.isoformat()[:10]}})
        # 4. pickups in the next 3 hours
        for r in db.execute(text("""
            SELECT p.order_id, o.user_id, p.scheduled_time, s.name FROM pickups p
            JOIN orders o ON o.id = p.order_id JOIN stores s ON s.id = p.store_id
            WHERE p.scheduled_time BETWEEN :a AND :b
        """), {"a": now, "b": now + timedelta(hours=3)}).fetchall():
            out.append({"type": "pickup_reminder", "user_id": str(r.user_id), "key": str(r.order_id),
                        "goal": "Remind the customer of their pickup time and store.",
                        "data": {"order_ref": str(r.order_id)[:8], "store": r.name, "time": r.scheduled_time.isoformat()}})
        keys = [f"{t['type']}:{t['key']}" for t in out]
        if keys:
            seen = {r.key for r in db.execute(text("SELECT key FROM proactive_triggers WHERE key = ANY(:k)"), {"k": keys}).fetchall()}
            out = [t for t in out if f"{t['type']}:{t['key']}" not in seen]
    return out[:MAX_TRIGGERS_PER_SCAN]


async def scan_and_act() -> Dict[str, Any]:
    from app.agentic.runtime import run_proactive
    released = release_expired_holds()
    try:
        trending = compute_trending()
    except Exception as e:
        log.warning("trending refresh failed: %s", e)
        trending = None
    triggers = find_triggers()
    results = []
    for t in triggers:
        key = f"{t['type']}:{t['key']}"
        with _db() as db:
            got = db.execute(text("""INSERT INTO proactive_triggers (key, user_id, type) VALUES (:k, :u, :t)
                                     ON CONFLICT (key) DO NOTHING RETURNING key"""),
                             {"k": key, "u": t["user_id"], "t": t["type"]}).first()
            db.commit()
        if not got:
            continue   # another worker took it
        try:
            res = await run_proactive(user_id=t["user_id"], trigger=t)
            status = "waiting_approval" if res.get("approval") else "done"
        except Exception as e:
            res, status = {"error": str(e)[:300]}, "failed"
        with _db() as db:
            db.execute(text("UPDATE proactive_triggers SET status = :s, result = CAST(:r AS jsonb) WHERE key = :k"),
                       {"s": status, "r": json.dumps({k: res.get(k) for k in ("reply", "plan", "approval", "error")}, default=str), "k": key})
            if t["type"] == "post_delivery_feedback" and status == "done":
                db.execute(text("UPDATE orders SET feedback_requested = TRUE WHERE id = :o"), {"o": t["key"]})
            db.commit()
        results.append({"key": key, "status": status})
    return {"released_holds": released, "trending": trending, "triggers": len(triggers), "results": results}

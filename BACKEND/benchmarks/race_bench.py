"""
Concurrent checkout race: legacy vs hardened stock reservation.

N shoppers, each with one unit of the same variant in their cart, hit
"reserve stock" at the same instant (threads released by a barrier, one DB
connection each, READ COMMITTED like production). We count how many holds
succeed, how many units were actually decremented, and whether the
inventory invariant total = reserved + assigned still holds.

    DATABASE_URL=postgresql://... python benchmarks/race_bench.py --stock 1 --shoppers 50 --trials 20

Uses its own bench_* rows; never run against production data you care about.
"""
import argparse
import json
import os
import statistics
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from benchmarks import legacy_reservation as legacy  # noqa: E402
from app.services import inventory_reservation_service as hardened  # noqa: E402

URL = os.environ["DATABASE_URL"]
engine = create_engine(URL, pool_size=80, max_overflow=20)
Session = sessionmaker(bind=engine)


def setup(stock: int, shoppers: int):
    vid = uuid.uuid4()
    with engine.begin() as c:
        pid = uuid.uuid4()
        c.execute(text("INSERT INTO products (id, name, brand, category, active, search_tsv) VALUES (:p, 'bench item', 'bench', 'bench', true, '')"), {"p": pid})
        c.execute(text("INSERT INTO product_variants (id, product_id, sku, base_price, active) VALUES (:v, :p, :s, 999, true)"),
                  {"v": vid, "p": pid, "s": f"BENCH-{vid.hex[:8]}"})
        c.execute(text("INSERT INTO global_inventory (product_variant_id, total_stock, reserved_stock, assigned_stock) VALUES (:v, :t, :t, 0)"),
                  {"v": vid, "t": stock})
        rows = []
        for _ in range(shoppers):
            uid, sid, cid, coid = (uuid.uuid4() for _ in range(4))
            c.execute(text("INSERT INTO users (id, name, email, role) VALUES (:u, 'bench', :e, 'user')"), {"u": uid, "e": f"{uid.hex[:10]}@bench.local"})
            c.execute(text("INSERT INTO sessions (id, user_id, primary_channel, active_channel, context) VALUES (:s, :u, 'web', 'web', '{}')"), {"s": sid, "u": uid})
            c.execute(text("INSERT INTO carts (id, user_id, session_id) VALUES (:c, :u, :s)"), {"c": cid, "u": uid, "s": sid})
            c.execute(text("INSERT INTO cart_items (cart_id, product_variant_id, quantity) VALUES (:c, :v, 1)"), {"c": cid, "v": vid})
            c.execute(text("""INSERT INTO checkout_sessions (id, user_id, session_id, cart_id, state, inventory_locked, payment_attempts, discount_amount)
                              VALUES (:co, :u, :s, :c, 'INIT', false, 0, 0)"""), {"co": coid, "u": uid, "s": sid, "c": cid})
            rows.append((coid, cid))
    return vid, rows


def attempt(fn, coid, cid, barrier, out, idx):
    db = Session()
    exp = datetime.now(timezone.utc) + timedelta(minutes=12)
    barrier.wait()
    t0 = time.perf_counter()
    try:
        fn(db, coid, cid, exp)
        db.commit()
        out[idx] = ("ok", (time.perf_counter() - t0) * 1000)
    except Exception as e:
        db.rollback()
        out[idx] = ("rejected" if "Not enough stock" in str(e) else f"error:{type(e).__name__}:{str(e)[:300]}", (time.perf_counter() - t0) * 1000)
    finally:
        db.close()


def trial(impl: str, stock: int, shoppers: int):
    fn = legacy.reserve_inventory_delivery if impl == "legacy" else hardened.reserve_inventory_delivery
    vid, rows = setup(stock, shoppers)
    barrier = threading.Barrier(shoppers)
    out = [None] * shoppers
    threads = [threading.Thread(target=attempt, args=(fn, coid, cid, barrier, out, i)) for i, (coid, cid) in enumerate(rows)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    with engine.connect() as c:
        inv = c.execute(text("SELECT total_stock, reserved_stock, assigned_stock FROM global_inventory WHERE product_variant_id = :v"), {"v": vid}).first()
        ledger = c.execute(text("SELECT coalesce(sum(quantity),0) FROM inventory_reservations WHERE product_variant_id = :v"), {"v": vid}).scalar()
    ok = sum(1 for o in out if o[0] == "ok")
    return {
        "impl": impl, "stock": stock, "shoppers": shoppers,
        "confirmed_holds": ok,                                   # checkouts told "your stock is held"
        "units_decremented": stock - inv.reserved_stock,         # what the inventory actually moved
        "ledger_units": int(ledger),                              # what the reservation ledger claims
        "phantom_holds": max(0, ok - (stock - inv.reserved_stock)),
        "oversold_units": max(0, int(ledger) - stock),
        "invariant_ok": inv.total_stock == inv.reserved_stock + inv.assigned_stock,
        "negative_stock": inv.reserved_stock < 0,
        "lat_ms": [o[1] for o in out],
        "errors": sum(1 for o in out if o[0].startswith("error")),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stock", type=int, default=1)
    ap.add_argument("--shoppers", type=int, default=50)
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "race_results.json"))
    a = ap.parse_args()
    results = []
    for impl in ("legacy", "hardened"):
        for _ in range(a.trials):
            results.append(trial(impl, a.stock, a.shoppers))
    summary = {}
    for impl in ("legacy", "hardened"):
        rs = [r for r in results if r["impl"] == impl]
        lat = sorted(x for r in rs for x in r["lat_ms"])
        summary[impl] = {
            "trials": len(rs),
            "mean_confirmed_holds": statistics.mean(r["confirmed_holds"] for r in rs),
            "mean_phantom_holds": statistics.mean(r["phantom_holds"] for r in rs),
            "mean_oversold_units": statistics.mean(r["oversold_units"] for r in rs),
            "trials_with_oversell": sum(1 for r in rs if r["oversold_units"] > 0),
            "invariant_violations": sum(1 for r in rs if not r["invariant_ok"]),
            "negative_stock_trials": sum(1 for r in rs if r["negative_stock"]),
            "errors": sum(r["errors"] for r in rs),
            "p50_ms": round(lat[len(lat) // 2], 2), "p95_ms": round(lat[int(len(lat) * 0.95)], 2),
        }
    print(json.dumps({"stock": a.stock, "shoppers": a.shoppers, "summary": summary}, indent=1))
    json.dump({"args": vars(a), "summary": summary, "trials": [{k: v for k, v in r.items() if k != "lat_ms"} for r in results]},
              open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

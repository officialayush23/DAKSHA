"""
Call every GET endpoint (and a few safe POSTs) as a customer and as an admin,
and report anything that returns 5xx. Path params are filled with real ids
from the database. Read-only: no writes except what GET handlers do.

    cd BACKEND && python scripts/api_sweep.py
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
os.environ.setdefault("PROACTIVE_ENABLED", "false")
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(HERE, "..", ".env"))
import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402


def tok(uid, email):
    now = int(time.time())
    return jwt.encode({"sub": uid, "email": email, "aud": "authenticated", "iat": now, "exp": now + 3600},
                      settings.SUPABASE_JWT_SECRET, algorithm="HS256")


with SessionLocal() as db:
    admin = db.execute(text("SELECT id, email FROM users WHERE role = 'admin' LIMIT 1")).first()
    cust = db.execute(text("""SELECT u.id, u.email FROM users u WHERE u.role = 'user'
                              AND EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id) LIMIT 1""")).first()
    ids = {
        "product_id": db.execute(text("SELECT id FROM products LIMIT 1")).scalar(),
        "variant_id": db.execute(text("SELECT id FROM product_variants LIMIT 1")).scalar(),
        "order_id": db.execute(text("SELECT id FROM orders WHERE user_id = :u LIMIT 1"), {"u": cust.id}).scalar(),
        "store_id": db.execute(text("SELECT id FROM stores LIMIT 1")).scalar(),
        "user_id": cust.id,
        "session_id": db.execute(text("SELECT id FROM chat_sessions WHERE user_id = :u LIMIT 1"), {"u": cust.id}).scalar(),
        "return_id": db.execute(text("SELECT id FROM returns LIMIT 1")).scalar(),
        "complaint_id": db.execute(text("SELECT id FROM complaints LIMIT 1")).scalar(),
        "run_id": db.execute(text("SELECT id FROM agent_runs ORDER BY started_at DESC LIMIT 1")).scalar(),
        "handoff_id": db.execute(text("SELECT id FROM agent_handoffs LIMIT 1")).scalar(),
        "kiosk_id": db.execute(text("SELECT id FROM kiosks LIMIT 1")).scalar(),
        "checkout_id": db.execute(text("SELECT id FROM checkout_sessions WHERE user_id = :u LIMIT 1"), {"u": cust.id}).scalar(),
    }

H = {"user": {"Authorization": f"Bearer {tok(str(cust.id), cust.email)}"},
     "admin": {"Authorization": f"Bearer {tok(str(admin.id), admin.email)}"}}
SKIP = {"/webhooks/telegram", "/user/telegram/link"}


def fill(path):
    def rep(m):
        name = m.group(1)
        key = {"id": "product_id", "pid": "product_id"}.get(name, name)
        if key not in ids:
            for k in ids:
                if k.split("_")[0] in name:
                    key = k
                    break
        return str(ids.get(key) or "00000000-0000-0000-0000-000000000000")
    return re.sub(r"\{([a-z_]+)\}", rep, path)


bad, ok = [], 0
with TestClient(app, raise_server_exceptions=False) as c:
    for r in app.routes:
        methods = getattr(r, "methods", None) or set()
        if "GET" not in methods or r.path in SKIP or r.path.startswith(("/docs", "/openapi", "/redoc")):
            continue
        who = "admin" if "/admin" in r.path or "agent-runs" in r.path else "user"
        url = fill(r.path)
        params = {}
        if "pickup/stores" in r.path:
            params = {"cart_id": ids["checkout_id"], "lat": 18.46, "lng": 73.86}
        if r.path.startswith("/stores/nearby"):
            params = {"lat": 18.46, "lng": 73.86}
        if "geocode" in r.path:
            params = {"q": "Pune", "query": "Pune", "address": "Pune", "lat": 18.46, "lng": 73.86, "place_id": "x"}
        t0 = time.perf_counter()
        resp = c.get(url, headers=H[who], params=params)
        ms = (time.perf_counter() - t0) * 1000
        if resp.status_code >= 500:
            bad.append((r.path, resp.status_code, resp.text[:200]))
            print(f"FAIL {resp.status_code} {who:5} {r.path}  {resp.text[:160]}")
        else:
            ok += 1
            print(f"ok   {resp.status_code} {who:5} {r.path} {ms:.0f}ms")
print(f"\n{ok} ok, {len(bad)} server errors")

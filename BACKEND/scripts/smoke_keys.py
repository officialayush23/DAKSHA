"""
Check every external dependency DAKSHA needs, without printing secrets.

    cd BACKEND && python scripts/smoke_keys.py

Each line prints OK / FAIL / SKIP and a short reason.
"""
import json
import os
import smtplib
import sys
import time

import httpx
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, "..", ".env"))
sys.path.insert(0, os.path.join(HERE, ".."))

E = lambda k: (os.getenv(k) or "").strip().strip('"').strip("'")
results = []


def check(name):
    def deco(fn):
        t0 = time.perf_counter()
        try:
            msg = fn()
            status = "SKIP" if (msg or "").startswith("skip") else "OK"
        except Exception as e:  # noqa
            status, msg = "FAIL", f"{type(e).__name__}: {str(e)[:220]}"
        ms = (time.perf_counter() - t0) * 1000
        results.append((name, status, msg))
        print(f"{status:4}  {name:28} {ms:7.0f} ms  {msg or ''}")
        return fn
    return deco


@check("postgres (DATABASE_URL)")
def _():
    from sqlalchemy import create_engine, text
    eng = create_engine(E("DATABASE_URL"), pool_pre_ping=True)
    with eng.connect() as c:
        n = c.execute(text("select count(*) from information_schema.tables where table_schema='public'")).scalar()
        ext = [r[0] for r in c.execute(text("select extname from pg_extension"))]
    return f"{n} public tables; ext={','.join(sorted(ext))}"


@check("postgres (LANGGRAPH_DB_URL)")
def _():
    if not E("LANGGRAPH_DB_URL"):
        return "skip: not set"
    import psycopg
    with psycopg.connect(E("LANGGRAPH_DB_URL"), connect_timeout=10) as c:
        c.execute("select 1")
    return "connected"


@check("redis")
def _():
    import redis
    r = redis.Redis.from_url(E("REDIS_URL"), socket_timeout=8)
    return f"ping={r.ping()}"


@check("supabase auth")
def _():
    r = httpx.get(f"{E('SUPABASE_URL')}/auth/v1/health", headers={"apikey": E("SUPABASE_ANON_KEY")}, timeout=10)
    r.raise_for_status()
    return f"http {r.status_code}"


@check("supabase storage")
def _():
    r = httpx.get(f"{E('SUPABASE_URL')}/storage/v1/bucket",
                  headers={"apikey": E("SUPABASE_SERVICE_ROLE_KEY"),
                           "Authorization": f"Bearer {E('SUPABASE_SERVICE_ROLE_KEY')}"}, timeout=10)
    r.raise_for_status()
    return "buckets=" + ",".join(b["name"] for b in r.json())


@check("nomic text embedding")
def _():
    import nomic
    from nomic import embed
    nomic.login(E("NOMIC_API_KEY"))
    model = E("NOMIC_TEXT_MODEL").replace("nomic-ai/", "") or "nomic-embed-text-v1.5"
    out = embed.text(texts=["red cotton kurta"], model=model, task_type="search_query", dimensionality=768)
    return f"{model} dim={len(out['embeddings'][0])}"


def _gemini(label, client):
    from google.genai import types
    model = E("GEMINI_MODEL") or "gemini-3.5-flash"
    cfg = types.GenerateContentConfig(response_mime_type="application/json")
    r = client.models.generate_content(model=model, contents='Return {"ok": true}', config=cfg)
    return f"{model} via {label}: {r.text.strip()[:40]}"


@check("gemini (api key, studio)")
def _():
    from google import genai
    key = E("GEMINI_API_KEY") or E("GEMINI_VERTEX_API_KEY")
    return _gemini("studio", genai.Client(api_key=key)) if key else "skip: no key"


@check("gemini (api key, vertex express)")
def _():
    from google import genai
    key = E("GEMINI_API_KEY") or E("GEMINI_VERTEX_API_KEY")
    return _gemini("vertex-express", genai.Client(vertexai=True, api_key=key)) if key else "skip: no key"


@check("gemini (vertex service acct)")
def _():
    raw = E("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not raw:
        return "skip: no SA json"
    import tempfile
    from google import genai
    p = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    p.write(raw); p.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = p.name
    c = genai.Client(vertexai=True, project=E("GOOGLE_CLOUD_PROJECT"),
                     location=E("GOOGLE_CLOUD_LOCATION") or "us-central1")
    return _gemini("vertex-sa", c)


@check("bedrock (xAI)")
def _():
    tok = E("AWS_BEARER_TOKEN_BEDROCK") or E("AWS_API_KEY_BEDROCK_FOR_XAI")
    if not tok:
        return "skip: no bedrock key"
    model = E("BEDROCK_MODEL_ID") or "us.xai.grok-4.7"
    region = E("AWS_REGION") or "us-east-1"
    r = httpx.post(f"https://bedrock-runtime.{region}.amazonaws.com/model/{model}/converse",
                   headers={"Authorization": f"Bearer {tok}"},
                   json={"messages": [{"role": "user", "content": [{"text": "Say OK"}]}],
                         "inferenceConfig": {"maxTokens": 10}}, timeout=40)
    if r.status_code != 200:
        raise RuntimeError(f"http {r.status_code}: {r.text[:160]}")
    txt = r.json()["output"]["message"]["content"][0]["text"]
    return f"{model}: {txt.strip()[:30]}"


@check("mapbox geocoding")
def _():
    tok = E("MAPBOX_TOKEN") or E("MAP_BOX_API_KEY")
    r = httpx.get("https://api.mapbox.com/search/geocode/v6/forward",
                  params={"q": "Shivajinagar, Pune", "country": "in", "limit": 1, "access_token": tok}, timeout=10)
    r.raise_for_status()
    f = r.json()["features"][0]
    return f"{f['properties']['full_address'][:50]}"


@check("google maps geocoding")
def _():
    key = E("GOOGLE_MAPS_API_KEY")
    if not key:
        return "skip: no key"
    r = httpx.get("https://maps.googleapis.com/maps/api/geocode/json",
                  params={"address": "Pune", "key": key}, timeout=10).json()
    if r.get("status") != "OK":
        raise RuntimeError(f"{r.get('status')}: {r.get('error_message', '')[:120]}")
    return "OK"


@check("resend")
def _():
    if not E("RESEND_API_KEY"):
        return "skip: no key"
    r = httpx.get("https://api.resend.com/domains", headers={"Authorization": f"Bearer {E('RESEND_API_KEY')}"}, timeout=10)
    if r.status_code >= 400:
        raise RuntimeError(f"http {r.status_code}: {r.text[:120]}")
    return f"http {r.status_code}"


@check("smtp login")
def _():
    if not E("SMTP_HOST"):
        return "skip: no host"
    s = smtplib.SMTP(E("SMTP_HOST"), int(E("SMTP_PORT") or 587), timeout=10)
    s.starttls(); s.login(E("SMTP_USERNAME"), E("SMTP_PASSWORD")); s.quit()
    return "login ok"


@check("telegram bot")
def _():
    if not E("TELEGRAM_TOKEN"):
        return "skip: no token"
    r = httpx.get(f"https://api.telegram.org/bot{E('TELEGRAM_TOKEN')}/getMe", timeout=10).json()
    if not r.get("ok"):
        raise RuntimeError(str(r)[:120])
    return "@" + r["result"]["username"]


if __name__ == "__main__":
    bad = [n for n, s, _ in results if s == "FAIL"]
    print("\n" + ("All checks passed." if not bad else f"{len(bad)} failing: " + ", ".join(bad)))

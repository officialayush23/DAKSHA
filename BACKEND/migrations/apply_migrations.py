"""
Apply DAKSHA SQL migrations (idempotent).

Usage:
    cd BACKEND
    python migrations/apply_migrations.py            # uses DATABASE_URL from .env
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
DB_URL = (os.getenv("LANGGRAPH_DB_URL") or os.getenv("DATABASE_URL") or "").strip().strip('"')
if not DB_URL:
    sys.exit("DATABASE_URL is not set")

MIGRATIONS = [
    ("v2", "v2_agent_graph_tables.sql"),
    ("v3", "v3_delivery_tracking.sql"),
    ("v4", "v4_policy_audit_indexes.sql"),
    ("v5", "v5_chat_sessions.sql"),
    ("v6", "v6_chat_message_ui_data.sql"),
    ("v7", "v7_agentic_core.sql"),
    ("v8", "v8_schema_drift.sql"),
]


def run(only=None):
    base = os.path.dirname(os.path.abspath(__file__))
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    for version, filename in MIGRATIONS:
        if only and version not in only:
            continue
        sql = open(os.path.join(base, filename), encoding="utf-8").read()
        print(f"Applying {filename} ...", end=" ")
        try:
            cur.execute(sql)
            print("ok")
        except Exception as e:
            print(f"FAILED: {e}")
            sys.exit(1)
    cur.close()
    conn.close()


if __name__ == "__main__":
    run(sys.argv[1:] or None)

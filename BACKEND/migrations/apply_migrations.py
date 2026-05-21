"""
Run this script from your local machine to apply all DAKSHA migrations.

Usage:
    cd BACKEND
    python migrations/apply_migrations.py
"""
import os, sys
import psycopg2

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:cKLdDhtigN4U0vxB@db.dxrtcwqupaplrbvjtohj.supabase.co:5432/postgres"
)

MIGRATIONS = [
    ("v2", "v2_agent_graph_tables.sql"),
    ("v3", "v3_delivery_tracking.sql"),
    ("v4", "v4_policy_audit_indexes.sql"),
]

def run():
    base = os.path.dirname(os.path.abspath(__file__))
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    for version, filename in MIGRATIONS:
        path = os.path.join(base, filename)
        sql = open(path).read()
        print(f"\n{'='*60}")
        print(f"Applying {filename} ...")
        try:
            cur.execute(sql)
            print(f"  ✅ {version} applied")
        except Exception as e:
            print(f"  ❌ {version} failed: {e}")
            sys.exit(1)

    cur.close()
    conn.close()
    print("\n✅ All migrations complete.")

if __name__ == "__main__":
    run()

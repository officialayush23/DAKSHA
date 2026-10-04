"""Compare app/models/models.py with the live database. Run: python scripts/check_schema_drift.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.models.models import Base  # noqa: E402

with engine.connect() as c:
    rows = c.execute(text("""SELECT table_name, column_name, is_nullable, column_default FROM information_schema.columns
                             WHERE table_schema = 'public'""")).fetchall()
db = {}
for t, col, nullable, default in rows:
    db.setdefault(t, {})[col] = (nullable, default)
problems = 0
for name, table in Base.metadata.tables.items():
    if name not in db:
        print("MISSING TABLE", name); problems += 1; continue
    for col in table.columns:
        if col.name not in db[name]:
            print("MISSING COLUMN", f"{name}.{col.name}", col.type); problems += 1
    for col, (nullable, default) in db[name].items():
        if col not in table.columns and nullable == "NO" and default is None:
            print("DB-ONLY NOT NULL WITHOUT DEFAULT", f"{name}.{col}"); problems += 1
print("schema OK" if not problems else f"{problems} drift issue(s)")

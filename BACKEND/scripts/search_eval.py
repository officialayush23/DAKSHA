"""
Search precision: legacy embedding-only search vs structured search.

    cd BACKEND && python scripts/search_eval.py

For each query we know the product type / colour the shopper asked for. A
result is "correct" if its catalog type (from catalog_taxonomy, which reads
the product name) and its variant colour match. Prints precision@k for both
pipelines and writes scripts/search_eval.json.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
os.environ.setdefault("PROACTIVE_ENABLED", "false")
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(HERE, "..", ".env"))

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.services import catalog_taxonomy as tx  # noqa: E402
from app.services.catalog_semantic_service import semantic_catalog_search  # noqa: E402
from app.services.structured_search_service import search  # noqa: E402

# (query, expected types, expected colours)
CASES = [
    ("help me find some tshirts", {"tshirt"}, set()),
    ("red t-shirts", {"tshirt"}, {"red"}),
    ("show me black jeans under 2000", {"jeans"}, {"black"}),
    ("jerseys", {"jersey"}, set()),
    ("red jersey", {"jersey"}, {"red"}),
    ("blue formal shirt for office", {"shirt"}, {"blue"}),
    ("hoodie", {"hoodie"}, set()),
    ("sneakers", {"sneakers"}, set()),
    ("running shoes", {"running_shoes"}, set()),
    ("footwear", {"sneakers", "running_shoes", "loafers"}, set()),
    ("pink kurti for women", {"kurta"}, {"pink"}),
    ("lehenga for a wedding", {"lehenga"}, set()),
    ("winter jacket", {"jacket"}, set()),
    ("grey track pants", {"track_pants"}, {"grey"}),
    ("white tee", {"tshirt"}, {"white"}),
    ("backpack for college", {"backpack"}, set()),
    ("maroon sherwani", {"sherwani"}, {"red"}),
    ("tshrt", {"tshirt"}, set()),                     # typo -> fuzzy
    ("denim", {"jeans"}, set()),
    ("yellow dress", {"dress"}, {"yellow"}),
]


def variant_meta(db, ids):
    if not ids:
        return {}
    rows = db.execute(text("""SELECT v.id::text vid, v.color, p.name, p.category, p.description
                              FROM product_variants v JOIN products p ON p.id = v.product_id
                              WHERE v.id::text = ANY(:ids)"""), {"ids": list(ids)}).mappings().all()
    return {r["vid"]: r for r in rows}


def correct(meta, types, colors):
    t = tx.classify_product(meta["name"], meta["category"], meta["description"])
    c = tx.color_of(meta["color"])
    return (not types or t in types) and (not colors or c in colors)


def main(k=5):
    report = []
    tot = {"legacy": [0, 0], "structured": [0, 0]}
    with SessionLocal() as db:
        for q, types, colors in CASES:
            t0 = time.perf_counter()
            legacy_ids = semantic_catalog_search(db, q, limit=k)
            t_leg = (time.perf_counter() - t0) * 1000
            t0 = time.perf_counter()
            res = search(db, q, limit=k, refine=False)
            t_new = (time.perf_counter() - t0) * 1000
            new_ids = [p["variant_id"] for p in res["products"]]
            meta = variant_meta(db, set(legacy_ids) | set(new_ids))
            leg_ok = sum(correct(meta[i], types, colors) for i in legacy_ids if i in meta)
            new_ok = sum(correct(meta[i], types, colors) for i in new_ids if i in meta)
            tot["legacy"][0] += leg_ok; tot["legacy"][1] += len(legacy_ids)
            tot["structured"][0] += new_ok; tot["structured"][1] += len(new_ids)
            row = {"query": q, "understood": res["understood"],
                   "legacy": [f"{meta[i]['name']} ({meta[i]['color']})" for i in legacy_ids if i in meta],
                   "structured": [f"{p['name']} ({p['color']})" for p in res["products"]],
                   "alternatives": [f"{p['name']} ({p['color']})" for p in res["related"]],
                   "legacy_precision": round(leg_ok / max(len(legacy_ids), 1), 2),
                   "structured_precision": round(new_ok / max(len(new_ids), 1), 2) if new_ids else None,
                   "legacy_ms": round(t_leg), "structured_ms": round(t_new)}
            report.append(row)
            print(f"\n{q!r}  ->  understood: {res['understood']}")
            print(f"   legacy     P@{k}={row['legacy_precision']:.2f}  {row['legacy']}")
            print(f"   structured P@{k}={row['structured_precision'] if new_ids else '-'}  {row['structured']}"
                  + (f"  | alternatives: {row['alternatives']}" if row["alternatives"] else ""))
    lp = tot["legacy"][0] / max(tot["legacy"][1], 1)
    sp = tot["structured"][0] / max(tot["structured"][1], 1)
    print(f"\nOVERALL precision@{k}: legacy {lp:.3f} ({tot['legacy'][0]}/{tot['legacy'][1]})  "
          f"structured {sp:.3f} ({tot['structured'][0]}/{tot['structured'][1]})")
    with open(os.path.join(HERE, "search_eval.json"), "w") as f:
        json.dump({"k": k, "legacy_precision": lp, "structured_precision": sp, "cases": report}, f, indent=2)


if __name__ == "__main__":
    main()

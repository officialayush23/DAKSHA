# app/services/structured_search_service.py
"""
Catalog search with hard filters and soft ranking.

    parse   catalog_taxonomy turns the request (plus any explicit agent hints)
            into filters: product type, colour, gender, size, brand, price
    refine  a follow-up that only adds attributes ("only red") keeps the
            product type from the previous search in the same session
    filter  every filter is applied as an exact check on catalog fields;
            nothing outside the filters can be returned as a match
    rank    inside the filtered set: Nomic text-embedding similarity to the
            request + keyword overlap (occasion, fabric, description)
    relax   if nothing matches, say so and offer clearly labelled
            alternatives (related types in the same colour, or the same
            type in other colours) instead of silently returning anything

Embeddings only ever order products that already satisfy the filters, so a
semantic near-miss (jeans for "t-shirts") cannot leak into the results.
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import replace
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services import catalog_taxonomy as tx

# per-session memory of the last search, for refinements like "only red"
_LAST: "OrderedDict[str, tx.QueryFilters]" = OrderedDict()
_LAST_LOCK = threading.Lock()


def _remember(key: Optional[str], f: tx.QueryFilters) -> None:
    if not key:
        return
    with _LAST_LOCK:
        _LAST[key] = f
        _LAST.move_to_end(key)
        while len(_LAST) > 1000:
            _LAST.popitem(last=False)


def _previous(key: Optional[str]) -> Optional[tx.QueryFilters]:
    if not key:
        return None
    with _LAST_LOCK:
        return _LAST.get(key)


_CAT_CACHE: dict = {"t": 0.0, "rows": None}
_CAT_TTL = 30.0


def _catalog(db: Session) -> List[dict]:
    import time
    if _CAT_CACHE["rows"] is not None and time.monotonic() - _CAT_CACHE["t"] < _CAT_TTL:
        return _CAT_CACHE["rows"]
    rows = db.execute(text("""
        SELECT v.id::text AS variant_id, v.product_id::text AS product_id, v.color, v.size,
               v.base_price, p.name, p.brand, p.category, p.gender, p.occasion, p.fabric_type,
               p.description,
               (SELECT pi.image_url FROM product_images pi WHERE pi.product_variant_id = v.id
                 ORDER BY pi.position LIMIT 1) AS image,
               GREATEST(COALESCE(gi.reserved_stock, 0), 0) + GREATEST(COALESCE(gi.assigned_stock, 0), 0) AS stock
        FROM product_variants v
        JOIN products p ON p.id = v.product_id
        LEFT JOIN global_inventory gi ON gi.product_variant_id = v.id
        WHERE v.active = true AND COALESCE(p.active, true) = true
    """)).mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        d["type"] = tx.product_type_cached(d["product_id"], d["name"], d["category"], d["description"])
        d["color_canon"] = tx.color_of(d["color"])
        d["gender_canon"] = tx.product_gender(d["gender"])
        out.append(d)
    _CAT_CACHE.update(t=time.monotonic(), rows=out)
    return out


def _gender_ok(item_gender: str, wanted: Optional[str]) -> bool:
    if not wanted:
        return True
    if wanted == "kids":
        return item_gender == "kids"
    return item_gender in (wanted, "unisex")


def _passes(d: dict, f: tx.QueryFilters, *, types=None, colors=None) -> bool:
    types = f.types if types is None else types
    colors = f.colors if colors is None else colors
    if d["stock"] <= 0:
        return False
    if types and d["type"] not in types:
        return False
    if colors and d["color_canon"] not in colors:
        return False
    if f.exclude_colors and d["color_canon"] in f.exclude_colors:
        return False
    if not _gender_ok(d["gender_canon"], f.gender):
        return False
    if f.sizes and (d["size"] or "").lower() not in f.sizes:
        return False
    if f.brands and (d["brand"] or "").lower() not in [b.lower() for b in f.brands]:
        return False
    return True


def _price(db: Session, d: dict, rules) -> dict:
    from app.services.pricing_service import resolve_variant_price
    return resolve_variant_price(db, variant_id=d["variant_id"], base_price=float(d["base_price"] or 0),
                                 brand=d["brand"], category=d["category"], rules_cache=rules)


def _semantic_scores(db: Session, ids: List[str], query: str) -> Dict[str, float]:
    if not ids or not query.strip():
        return {}
    from app.services.embedding_service import generate_text_embedding
    vec = generate_text_embedding(query, task_type="search_query")
    if not any(vec):
        return {}
    rows = db.execute(text("""
        SELECT product_variant_id::text AS vid, 1 - (embedding <=> CAST(:vec AS vector)) AS sim
        FROM product_multimodal_embeddings
        WHERE modality = 'text' AND product_variant_id::text = ANY(:ids)
    """), {"vec": str(vec), "ids": ids}).fetchall()
    return {r.vid: float(r.sim) for r in rows}


def _keyword_score(d: dict, keywords: List[str]) -> float:
    if not keywords:
        return 0.0
    hay = " ".join(str(d.get(k) or "") for k in ("name", "occasion", "fabric_type", "description", "category")).lower()
    return sum(1 for k in keywords if k in hay) / len(keywords)


def _card(d: dict, price: dict, match: str) -> dict:
    return {
        "variant_id": d["variant_id"], "product_id": d["product_id"], "name": d["name"], "brand": d["brand"],
        "category": d["category"], "type": tx.type_label(d["type"]) if d["type"] else None,
        "color": d["color"], "size": d["size"], "image": d["image"],
        "price": price["final_price"], "base_price": price["base_price"], "final_price": price["final_price"],
        "offer_name": price.get("offer_name"), "in_stock": int(d["stock"]), "match": match,
    }


def _select(db: Session, pool: List[dict], f: tx.QueryFilters, query: str, limit: int, rules, match: str,
            one_per_product: bool) -> List[dict]:
    priced = []
    for d in pool:
        p = _price(db, d, rules)
        if f.max_price is not None and p["final_price"] > f.max_price:
            continue
        if f.min_price is not None and p["final_price"] < f.min_price:
            continue
        priced.append((d, p))
    # Embeddings are only needed to order free text the filters didn't consume
    # ("for a wedding", "breathable"). A pure "red t-shirts" query skips the
    # remote embedding call entirely, which keeps search instant.
    sem = _semantic_scores(db, [d["variant_id"] for d, _ in priced], query) if (f.keywords or not f.types) else {}
    scored = sorted(priced, key=lambda dp: (-(0.7 * sem.get(dp[0]["variant_id"], 0.0)
                                               + 0.3 * _keyword_score(dp[0], f.keywords)),
                                             -int(dp[0]["stock"] or 0), dp[0]["name"]))
    # open-ended queries ("something for a wedding") have no hard filters, so
    # keep only items close to the best semantic match instead of the catalog
    if sem and not f.has_constraints():
        best = max(sem.values())
        scored = [dp for dp in scored if sem.get(dp[0]["variant_id"], 0.0) >= best - 0.08]
    out, seen = [], set()
    for d, p in scored:
        if one_per_product and d["product_id"] in seen:
            continue
        seen.add(d["product_id"])
        out.append(_card(d, p, match))
        if len(out) >= limit:
            break
    return out


def search(db: Session, query: str, *, product_type: Optional[str] = None, color: Optional[str] = None,
           exclude_color: Optional[str] = None, gender: Optional[str] = None, size: Optional[str] = None,
           brand: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None,
           limit: int = 8, session_key: Optional[str] = None, refine: bool = True) -> dict:
    """
    Returns {"products": [...], "related": [...], "filters": {...}, "summary": str}.
    `products` satisfy every filter; `related` are clearly labelled alternatives.
    """
    from app.models.models import ProductDiscountRule  # noqa: F401  (rules cache below)
    catalog = _catalog(db)
    brands = sorted({c["brand"] for c in catalog if c["brand"]})
    f = tx.parse_query(query or "", known_brands=brands)

    # explicit hints from the agent override what the parser read
    if product_type:
        t = tx.normalize_type(product_type)
        if t:
            f.types, f.type_source = t, "agent"
    if color:
        c = tx.normalize_color(color)
        if c:
            f.colors = c
    if exclude_color:
        f.exclude_colors = tx.normalize_color(exclude_color)
    if gender:
        f.gender = tx.normalize_gender(gender) or f.gender
    if size:
        f.sizes = [size.lower()]
    if brand:
        f.brands = [b for b in brands if b.lower() == brand.lower()] or [brand]
    if min_price:
        f.min_price = min_price
    if max_price:
        f.max_price = max_price

    # refinement: "only red" after "t-shirts" keeps the t-shirt filter
    prev = _previous(session_key) if refine else None
    inherited = False
    if prev and not f.types and not f.keywords and (f.colors or f.sizes or f.gender or f.max_price or f.min_price
                                                     or f.exclude_colors or f.brands):
        f = replace(f, types=list(prev.types), gender=f.gender or prev.gender,
                    min_price=f.min_price or prev.min_price, max_price=f.max_price or prev.max_price)
        inherited = bool(prev.types)
    _remember(session_key, f)

    from app.services.pricing_service import resolve_variant_price  # noqa: F401
    rules = None
    try:
        from datetime import datetime
        from sqlalchemy import or_
        now = datetime.utcnow()
        rules = db.query(ProductDiscountRule).filter(
            ProductDiscountRule.active.is_(True), ProductDiscountRule.valid_from <= now,
            or_(ProductDiscountRule.valid_to.is_(None), ProductDiscountRule.valid_to >= now)).all()
    except Exception:
        rules = None

    rank_text = query or f.describe()
    one_per_product = not f.colors and not f.sizes
    exact_pool = [d for d in catalog if _passes(d, f)]
    products = _select(db, exact_pool, f, rank_text, limit, rules, "exact", one_per_product)

    related: List[dict] = []
    relax_note = ""
    if len(products) < 3 and f.types:
        rel_types = [t for base in f.types for t in tx.RELATED_TYPES.get(base, []) if t not in f.types]
        if rel_types:
            pool = [d for d in catalog if _passes(d, f, types=rel_types)]
            related = _select(db, pool, f, rank_text, max(0, 4 - len(products)) or 2, rules, "related", one_per_product)
        if not products and not related and f.colors:
            pool = [d for d in catalog if _passes(d, f, colors=[])]
            related = _select(db, pool, f, rank_text, 4, rules, "other-colour", True)
            relax_note = f"no {'/'.join(f.colors)} in stock; showing other colours"

    want = f.describe()
    if products:
        summary = f"{len(products)} exact matches for {want}"
    else:
        summary = f"no exact matches for {want}"
    if inherited:
        summary += " (kept the product type from the previous search)"
    if related:
        summary += f"; {len(related)} labelled alternatives" + (f" ({relax_note})" if relax_note else "")
    if f.notes:
        summary += "; " + "; ".join(f.notes)

    return {"products": products, "related": related, "filters": f.to_dict(), "summary": summary,
            "understood": want}

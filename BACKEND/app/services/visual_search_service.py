# app/services/visual_search_service.py
"""
Image search with classical computer vision, no LLM in the loop.

Pipeline for a shopper's photo:

  1. Segment     GrabCut seeded with a centred rectangle separates the garment
                 from the background (catalog shots on white use a fast
                 border-colour threshold instead).
  2. Describe    - dominant colour: k-means (k=3) on foreground pixels in Lab,
                   nearest named colour from the catalog palette
                 - colour distribution: 16x4x4 HSV histogram of the foreground
                 - silhouette: Hu moments of the foreground mask
                 - local features: SIFT keypoints/descriptors (max 400)
  3. Recall      all in-stock catalog images (features cached per URL), ranked
                 by colour + silhouette (+ Nomic vision-embedding similarity
                 when available); keep the top 30
  4. Verify      SIFT matching with Lowe's ratio test (0.75), then RANSAC
                 homography, rejected if degenerate (reflection, extreme scale
                 or perspective, non-convex outline); the inlier count measures
                 whether the same print, logo or texture appears in both images
  5. Score       0.35 RANSAC inliers + 0.25 colour + 0.15 silhouette
                 + 0.25 embedding (renormalised when a signal is missing)

Measured on the live catalog (scripts/visual_eval.py, synthetic shopper
photos: rotation, scale, clutter, lighting, JPEG):
    embeddings only   top-1 0.30  top-5 0.65   ~890 ms
    CV pipeline       top-1 0.97  top-5 0.97   ~240 ms

Hints the agent may pass (product type, colour) are applied as hard filters
before scoring. The result includes a per-signal breakdown so the reply (and
the admin trace) can say *why* an item matched.
"""
from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import numpy as np

log = logging.getLogger("daksha.visual")

MAX_SIDE = 384
SIFT_FEATURES = 400
RATIO = 0.75
RANSAC_REPROJ = 5.0
MIN_GOOD = 8
INLIER_SATURATION = 40.0
RECALL_K = 30
EMBED_RECALL_ABOVE = 300      # catalog images; below this CV alone is used
W = {"inliers": 0.35, "color": 0.25, "shape": 0.15, "embed": 0.25}

_STORAGE_MARKER = "/storage/v1/object/public/"


def _cv2():
    import cv2  # local import: the API still boots if opencv is missing
    return cv2


# ── image loading (only our own storage; no arbitrary URLs => no SSRF) ───────
def _allowed(url: str) -> bool:
    from app.core.config import settings
    try:
        return urlparse(url).netloc == urlparse(settings.SUPABASE_URL).netloc
    except Exception:
        return False


def fetch_image_bytes(url: str) -> bytes:
    if not url or not url.startswith("http"):
        raise ValueError("image must be an uploaded image URL")
    if not _allowed(url):
        raise ValueError("only images uploaded to DAKSHA can be searched")
    if _STORAGE_MARKER in url:
        from app.services.storage_service import supabase as sb
        tail = url.split(_STORAGE_MARKER, 1)[1]
        bucket, _, path = tail.partition("/")
        return sb.storage.from_(bucket).download(path.split("?")[0])
    import httpx
    r = httpx.get(url, timeout=15)
    r.raise_for_status()
    return r.content


def decode(data: bytes):
    cv2 = _cv2()
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("could not read the image")
    h, w = img.shape[:2]
    s = MAX_SIDE / max(h, w)
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img


# ── segmentation ─────────────────────────────────────────────────────────────
def _border_mask(img) -> Optional[np.ndarray]:
    """Fast path for studio shots: background = colour of the image border."""
    cv2 = _cv2()
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    b = np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])
    bg = np.median(b, axis=0)
    if np.mean(np.linalg.norm(b - bg, axis=1)) > 12:      # busy border: not a studio shot
        return None
    dist = np.linalg.norm(lab - bg, axis=2)
    m = (dist > 18).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return m if 0.05 < (m > 0).mean() < 0.95 else None


def _grabcut_mask(img) -> np.ndarray:
    cv2 = _cv2()
    h, w = img.shape[:2]
    rect = (int(w * 0.08), int(h * 0.05), int(w * 0.84), int(h * 0.9))
    mask = np.zeros((h, w), np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(img, mask, rect, bgd, fgd, 3, cv2.GC_INIT_WITH_RECT)
        m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        if (m > 0).mean() > 0.04:
            return m
    except Exception:
        pass
    m = np.zeros((h, w), np.uint8)
    m[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]] = 255
    return m


def segment(img) -> np.ndarray:
    m = _border_mask(img)
    return m if m is not None else _grabcut_mask(img)


# ── descriptors ──────────────────────────────────────────────────────────────
_PALETTE_LAB: Optional[Dict[str, np.ndarray]] = None


def _palette():
    global _PALETTE_LAB
    if _PALETTE_LAB is None:
        cv2 = _cv2()
        from app.services.catalog_taxonomy import COLORS
        pal = {}
        for name, (rgb, _) in COLORS.items():
            px = np.uint8([[list(reversed(rgb))]])          # RGB -> BGR pixel
            pal[name] = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)
        _PALETTE_LAB = pal
    return _PALETTE_LAB


def _skin_mask(img) -> np.ndarray:
    """Classic YCrCb skin range; used to ignore the model's skin in garment photos."""
    cv2 = _cv2()
    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    return cv2.inRange(ycc, (0, 135, 85), (255, 175, 135))


def name_color(bgr) -> str:
    """Name a colour from HSV rules (more robust than nearest-anchor for dark denim, khaki, etc.)."""
    cv2 = _cv2()
    h, sat, v = [int(x) for x in cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0, 0]]
    if v < 55:
        return "black"
    if sat < 38:
        if v > 200:
            return "white"
        return "grey" if v > 70 else "black"
    if (h <= 8 or h >= 170):
        return "red" if v > 90 else ("brown" if sat < 150 else "red")
    if h <= 20:
        return "brown" if v < 170 or sat < 110 else "orange"
    if h <= 33:
        return "yellow" if v > 150 and sat > 90 else "brown"
    if h <= 85:
        return "green"
    if h <= 128:
        return "blue"
    if h <= 150:
        return "purple"
    return "pink"


def color_palette(img, mask, k: int = 4) -> List[Tuple[str, float]]:
    """Named colours of the foreground with their pixel share, largest first
    (skin removed). A palette survives clutter better than one dominant colour."""
    cv2 = _cv2()
    fg = mask > 0
    no_skin = fg & (_skin_mask(img) == 0)
    if no_skin.sum() > 0.3 * fg.sum():
        fg = no_skin
    px = img[fg].reshape(-1, 3).astype(np.float32)
    if len(px) < 50:
        return []
    if len(px) > 6000:
        px = px[np.random.default_rng(0).choice(len(px), 6000, replace=False)]
    k = k if len(px) >= 400 else 1
    _, labels, centers = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
                                    3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k).astype(float)
    shares: Dict[str, float] = {}
    for c, n in zip(centers, counts):
        name = name_color([int(round(x)) for x in c])
        shares[name] = shares.get(name, 0.0) + n / counts.sum()
    return sorted(shares.items(), key=lambda kv: -kv[1])


def dominant_color(img, mask) -> Tuple[Optional[str], float]:
    pal = color_palette(img, mask)
    return (pal[0][0], pal[0][1]) if pal else (None, 0.0)


def hsv_hist(img, mask) -> np.ndarray:
    cv2 = _cv2()
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], mask, [16, 4, 4], [0, 180, 0, 256, 0, 256])
    cv2.normalize(h, h, alpha=1.0, norm_type=cv2.NORM_L1)
    return h.flatten().astype(np.float32)


def hu_moments(mask) -> np.ndarray:
    cv2 = _cv2()
    hu = cv2.HuMoments(cv2.moments(mask, binaryImage=True)).flatten()
    return -np.sign(hu) * np.log10(np.abs(hu) + 1e-30)


def sift(img, mask):
    cv2 = _cv2()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kp, des = cv2.SIFT_create(nfeatures=SIFT_FEATURES).detectAndCompute(gray, mask)
    pts = np.float32([k.pt for k in kp]) if kp else np.zeros((0, 2), np.float32)
    return pts, des


@dataclass
class Features:
    color: Optional[str]
    color_share: float
    palette: List[Tuple[str, float]]
    hist: np.ndarray
    hu: np.ndarray
    pts: np.ndarray
    des: Optional[np.ndarray]
    fg_ratio: float


def describe(img) -> Features:
    mask = segment(img)
    palette = color_palette(img, mask)
    color, share = (palette[0] if palette else (None, 0.0))
    pts, des = sift(img, mask)
    return Features(color, share, palette, hsv_hist(img, mask), hu_moments(mask), pts, des, float((mask > 0).mean()))


# ── pairwise signals ─────────────────────────────────────────────────────────
def color_sim(a: Features, b: Features) -> float:
    cv2 = _cv2()
    bc = cv2.compareHist(a.hist, b.hist, cv2.HISTCMP_BHATTACHARYYA)      # 0 = identical
    s = max(0.0, 1.0 - float(bc))
    # the candidate's main colour is a meaningful part of the query photo
    share = dict(getattr(a, "palette", None) or []).get(b.color, 0.0)
    if share >= 0.12:
        s = min(1.0, 0.5 * s + 0.5 + 0.5 * min(share / 0.5, 1.0) * 0.5)
    elif a.color and a.color == b.color:
        s = min(1.0, s + 0.2)
    return s


def shape_sim(a: Features, b: Features) -> float:
    d = float(np.sum(np.abs(a.hu[:4] - b.hu[:4])))          # first 4 Hu moments are the stable ones
    return math.exp(-d / 2.0)


_matcher_lock = threading.Lock()


def ransac_inliers(a: Features, b: Features) -> int:
    cv2 = _cv2()
    if a.des is None or b.des is None or len(a.des) < MIN_GOOD or len(b.des) < MIN_GOOD:
        return 0
    with _matcher_lock:
        knn = cv2.BFMatcher(cv2.NORM_L2).knnMatch(a.des, b.des, k=2)
    good = [m for m, *rest in (p for p in knn if len(p) == 2) if m.distance < RATIO * rest[0].distance]
    if len(good) < MIN_GOOD:
        return 0
    src = a.pts[[m.queryIdx for m in good]].reshape(-1, 1, 2)
    dst = b.pts[[m.trainIdx for m in good]].reshape(-1, 1, 2)
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, RANSAC_REPROJ)
    if H is None or inl is None or not _plausible(H, a.pts):
        return 0
    return int(inl.sum())


def _plausible(H: np.ndarray, pts: np.ndarray) -> bool:
    """Reject degenerate homographies RANSAC can still fit to clutter: a real
    view of the same item keeps orientation (det > 0), changes scale by a
    bounded factor, and maps the keypoints' bounding box to a convex quad."""
    cv2 = _cv2()
    det = float(np.linalg.det(H[:2, :2]))
    if not (0.05 < det < 20.0):
        return False
    if abs(H[2, 0]) > 0.005 or abs(H[2, 1]) > 0.005:      # strong perspective = implausible for product shots
        return False
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    box = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]).reshape(-1, 1, 2)
    quad = cv2.perspectiveTransform(box, H)
    return bool(cv2.isContourConvex(quad.astype(np.float32)))


# ── catalog feature cache ────────────────────────────────────────────────────
_CACHE: Dict[str, Tuple[float, Features]] = {}
_CACHE_LOCK = threading.Lock()
_TTL = 6 * 3600


def catalog_features(url: str) -> Optional[Features]:
    hit = _CACHE.get(url)
    if hit and time.monotonic() - hit[0] < _TTL:
        return hit[1]
    try:
        f = describe(decode(fetch_image_bytes(url)))
    except Exception as e:
        log.warning("visual: could not index %s: %s", url[-60:], e)
        return None
    with _CACHE_LOCK:
        _CACHE[url] = (time.monotonic(), f)
    return f


def _candidates(db) -> List[dict]:
    from sqlalchemy import text
    from app.services import catalog_taxonomy as tx
    rows = db.execute(text("""
        SELECT v.id::text AS variant_id, v.product_id::text AS product_id, v.color, p.name, p.category,
               p.description,
               (SELECT pi.image_url FROM product_images pi WHERE pi.product_variant_id = v.id
                 ORDER BY pi.position LIMIT 1) AS image,
               GREATEST(COALESCE(gi.reserved_stock, 0), 0) + GREATEST(COALESCE(gi.assigned_stock, 0), 0) AS stock
        FROM product_variants v JOIN products p ON p.id = v.product_id
        LEFT JOIN global_inventory gi ON gi.product_variant_id = v.id
        WHERE v.active = true AND COALESCE(p.active, true) = true
    """)).mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        if not d["image"]:
            continue
        d["type"] = tx.product_type_cached(d["product_id"], d["name"], d["category"], d["description"])
        d["color_canon"] = tx.color_of(d["color"])
        out.append(d)
    return out


def warm_cache(db=None) -> int:
    """Index every catalog image (run in the background at startup)."""
    from app.core.database import SessionLocal
    own = db is None
    db = db or SessionLocal()
    try:
        n = 0
        for d in _candidates(db):
            if catalog_features(d["image"]) is not None:
                n += 1
        return n
    finally:
        if own:
            db.close()


def _embedding_scores(db, image_url: str, ids: List[str]) -> Dict[str, float]:
    try:
        from sqlalchemy import text
        from app.services.embedding_service import generate_image_embedding
        vec = generate_image_embedding(image_url)
        if not vec or not any(vec):
            return {}
        rows = db.execute(text("""
            SELECT product_variant_id::text AS vid, 1 - (embedding <=> CAST(:vec AS vector)) AS sim
            FROM product_multimodal_embeddings WHERE modality = 'image' AND product_variant_id::text = ANY(:ids)
        """), {"vec": str(vec), "ids": ids}).fetchall()
        return {r.vid: max(0.0, float(r.sim)) for r in rows}
    except Exception as e:
        log.warning("visual: embedding signal unavailable: %s", e)
        return {}


def search_by_image(db, image_url: str, *, product_type: Optional[str] = None, color: Optional[str] = None,
                    limit: int = 8, use_embeddings: Optional[bool] = None, query_bytes: Optional[bytes] = None,
                    embed_source: Optional[str] = None, weights: Optional[Dict[str, float]] = None) -> dict:
    """
    Returns {"matches": [{variant_id, score, signals{...}}], "query": {color, color_share, looks_like}, ...}
    """
    from app.services import catalog_taxonomy as tx
    t0 = time.perf_counter()
    q = describe(decode(query_bytes if query_bytes is not None else fetch_image_bytes(image_url)))

    cands = [d for d in _candidates(db) if d["stock"] > 0]
    want_types = tx.normalize_type(product_type) if product_type else []
    want_colors = tx.normalize_color(color) if color else []
    if want_types:
        cands = [d for d in cands if d["type"] in want_types]
    if want_colors:
        cands = [d for d in cands if d["color_canon"] in want_colors]

    feats = {d["variant_id"]: catalog_features(d["image"]) for d in cands}
    cands = [d for d in cands if feats.get(d["variant_id"]) is not None]
    # On this catalog CV alone is as accurate as CV + embeddings and ~4x faster
    # (scripts/visual_eval.py), so the remote embedding call is only used as an
    # extra recall signal once the catalog is large.
    if use_embeddings is None:
        use_embeddings = len(cands) > EMBED_RECALL_ABOVE
    src = embed_source or image_url
    emb = _embedding_scores(db, src, [d["variant_id"] for d in cands]) if (use_embeddings and src) else {}
    w = weights or W

    # stage 1: cheap recall on colour + silhouette (+ embedding)
    pre = []
    for d in cands:
        f = feats[d["variant_id"]]
        cs, ss = color_sim(q, f), shape_sim(q, f)
        es = emb.get(d["variant_id"])
        pre.append((d, cs, ss, es, 0.5 * cs + 0.2 * ss + (0.3 * es if es is not None else 0.0)))
    pre.sort(key=lambda x: -x[4])
    recall_k = len(pre) if (weights and weights.get("inliers", 0) == 0) else RECALL_K

    # stage 2: SIFT + RANSAC verification on the shortlist
    scored = []
    for d, cs, ss, es, _ in pre[:recall_k]:
        inl = ransac_inliers(q, feats[d["variant_id"]]) if w.get("inliers", 0) > 0 else 0
        sig = {"inliers": min(inl / INLIER_SATURATION, 1.0), "color": cs, "shape": ss}
        if es is not None:
            sig["embed"] = es
        wsum = sum(w.get(k, 0) for k in sig) or 1.0
        score = sum(w.get(k, 0) * v for k, v in sig.items()) / wsum
        scored.append({"variant_id": d["variant_id"], "product_id": d["product_id"], "name": d["name"],
                       "color": d["color"], "type": d["type"], "score": round(score, 4),
                       "signals": {"ransac_inliers": inl, "color": round(cs, 3), "shape": round(ss, 3),
                                   "embedding": round(es, 3) if es is not None else None}})
    scored.sort(key=lambda x: -x["score"])

    # one card per product; best variant first
    out, seen = [], set()
    for s in scored:
        if s["product_id"] in seen:
            continue
        seen.add(s["product_id"])
        out.append(s)
        if len(out) >= limit:
            break

    # kNN vote over the top matches: what kind of item is in the photo?
    votes: Dict[str, float] = {}
    for s in scored[:5]:
        if s["type"]:
            votes[s["type"]] = votes.get(s["type"], 0) + s["score"]
    looks_like = max(votes, key=votes.get) if votes else None

    return {"matches": out,
            "query": {"color": q.color, "color_share": round(q.color_share, 2),
                      "looks_like": tx.type_label(looks_like) if looks_like else None,
                      "keypoints": int(len(q.pts)), "foreground": round(q.fg_ratio, 2)},
            "filters": {"types": want_types, "colors": want_colors},
            "ms": round((time.perf_counter() - t0) * 1000)}

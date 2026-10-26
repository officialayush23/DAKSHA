"""
Image-search evaluation on the real catalog.

    cd BACKEND && python scripts/visual_eval.py [--n 40] [--modes cv,embed,combined]

Every catalog photo is turned into a synthetic "shopper photo" (rotation,
scale, crop, brightness/contrast, cluttered background, JPEG) and searched.
A hit means the original product is returned. Catalog features are cached in
scripts/.visual_cache.pkl between runs. Writes scripts/visual_eval.json.
"""
import argparse
import json
import os
import pickle
import random
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
os.environ.setdefault("PROACTIVE_ENABLED", "false")
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(HERE, "..", ".env"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.services import catalog_taxonomy as tx  # noqa: E402
from app.services import visual_search_service as vs  # noqa: E402

CACHE = os.path.join(HERE, ".visual_cache.pkl")
MODES = {
    "cv":       {"inliers": 0.35, "color": 0.25, "shape": 0.15},
    "embed":    {"embed": 1.0},
    "combined": dict(vs.W),
}


def augment(img, rng):
    h, w = img.shape[:2]
    bg = np.zeros((int(h * 1.35), int(w * 1.35), 3), np.uint8)
    base = rng.integers(40, 220, 3)
    bg[:] = base
    noise = rng.normal(0, 18, bg.shape)
    for _ in range(6):   # clutter: random rectangles
        x, y = rng.integers(0, bg.shape[1] - 20), rng.integers(0, bg.shape[0] - 20)
        cv2.rectangle(bg, (int(x), int(y)), (int(x + rng.integers(20, 120)), int(y + rng.integers(20, 120))),
                      tuple(int(c) for c in rng.integers(0, 255, 3)), -1)
    bg = np.clip(bg + noise, 0, 255).astype(np.uint8)
    s = rng.uniform(0.7, 0.95)
    small = cv2.resize(img, (int(w * s), int(h * s)))
    M = cv2.getRotationMatrix2D((small.shape[1] / 2, small.shape[0] / 2), rng.uniform(-12, 12), 1.0)
    rot = cv2.warpAffine(small, M, (small.shape[1], small.shape[0]), borderValue=(255, 255, 255))
    # drop the studio white so the item sits on the cluttered background
    mask = (cv2.cvtColor(rot, cv2.COLOR_BGR2GRAY) < 235).astype(np.uint8)
    oy = int(rng.integers(0, bg.shape[0] - rot.shape[0])); ox = int(rng.integers(0, bg.shape[1] - rot.shape[1]))
    roi = bg[oy:oy + rot.shape[0], ox:ox + rot.shape[1]]
    roi[mask > 0] = rot[mask > 0]
    out = cv2.convertScaleAbs(bg, alpha=rng.uniform(0.8, 1.2), beta=rng.uniform(-25, 25))
    ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return buf.tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--modes", default="cv,embed,combined")
    ap.add_argument("--index-only", action="store_true")
    args = ap.parse_args()
    if os.path.exists(CACHE):
        vs._CACHE.update({k: (time.monotonic(), v[1]) for k, v in pickle.load(open(CACHE, "rb")).items()})
    rng = np.random.default_rng(7)
    with SessionLocal() as db:
        cands = [d for d in vs._candidates(db) if d["stock"] > 0]
        t0 = time.perf_counter()
        for d in cands:
            vs.catalog_features(d["image"])
        pickle.dump({k: (0.0, v[1]) for k, v in vs._CACHE.items()}, open(CACHE, "wb"))
        print(f"indexed {len(vs._CACHE)} catalog images in {time.perf_counter() - t0:.1f}s")
        if args.index_only:
            return
        # one query per product (first in-stock variant), deterministic order
        seen, queries = set(), []
        for d in sorted(cands, key=lambda x: x["variant_id"]):
            if d["product_id"] not in seen:
                seen.add(d["product_id"]); queries.append(d)
        queries = queries[: args.n]
        results = {}
        for mode in args.modes.split(","):
            hit1 = hit5 = type1 = color_ok = 0
            times = []
            for i, d in enumerate(queries):
                img = vs.decode(vs.fetch_image_bytes(d["image"]))
                qb = augment(img, np.random.default_rng(1000 + i))
                tmp = None
                if mode != "cv":
                    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False); tmp.write(qb); tmp.close()
                t0 = time.perf_counter()
                res = vs.search_by_image(db, None, query_bytes=qb, use_embeddings=(mode != "cv"),
                                         embed_source=tmp.name if tmp else None, weights=MODES[mode], limit=5)
                times.append((time.perf_counter() - t0) * 1000)
                if tmp:
                    os.unlink(tmp.name)
                pids = [m["product_id"] for m in res["matches"]]
                hit1 += bool(pids) and pids[0] == d["product_id"]
                hit5 += d["product_id"] in pids
                type1 += bool(res["matches"]) and res["matches"][0]["type"] == d["type"]
                color_ok += res["query"]["color"] == d["color_canon"]
            n = len(queries)
            results[mode] = {"n": n, "top1": round(hit1 / n, 3), "top5": round(hit5 / n, 3),
                             "type_top1": round(type1 / n, 3), "color_detect": round(color_ok / n, 3),
                             "median_ms": round(float(np.median(times)))}
            print(mode, results[mode])
    with open(os.path.join(HERE, "visual_eval.json"), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()

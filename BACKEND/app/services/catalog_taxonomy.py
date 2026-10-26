# app/services/catalog_taxonomy.py
"""
Deterministic understanding of shopping queries and catalog items.

The LLM agent only says *what* to look for ("t-shirt", "red", "under 2000").
This module turns that into exact, checkable filters, so a request for red
t-shirts can never return jeans:

  1. Lexicon      - canonical product types, colours, genders with synonyms
                    (t-shirt / tee / tshirt -> tshirt; maroon / crimson -> red).
  2. Fuzzy match  - difflib ratio for typos ("tshrt", "jens", "sneekers").
  3. Zero-shot    - only for words neither step knows: cosine similarity of
                    the Nomic text embedding against embedded type prototypes,
                    accepted only above a strict threshold. No training data.

Catalog items get a product type the same way (from name, then category), so
the messy `category` column ("Clothing", "T shirt", "Men") never decides
what a product is.
"""
from __future__ import annotations

import difflib
import math
import re
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

# ── Product types ────────────────────────────────────────────────────────────
# canonical type -> (display label, synonyms). Multi-word synonyms are matched
# before single words, longest first.
PRODUCT_TYPES: Dict[str, Tuple[str, List[str]]] = {
    "tshirt":      ("T-shirt",      ["t-shirt", "t shirt", "tshirt", "tee", "tees", "polo", "polo shirt", "polo t-shirt", "crew neck"]),
    "shirt":       ("Shirt",        ["shirt", "formal shirt", "linen shirt", "button down", "button-down", "dress shirt"]),
    "jersey":      ("Jersey",       ["jersey", "sports jersey", "football jersey", "sports tee"]),
    "hoodie":      ("Hoodie",       ["hoodie", "hoody", "hooded sweatshirt", "sweatshirt"]),
    "sweater":     ("Sweater",      ["sweater", "jumper", "pullover", "cardigan", "woolen", "woollen"]),
    "jacket":      ("Jacket",       ["jacket", "denim jacket", "puffer", "puffer jacket", "bomber", "windcheater", "parka", "coat"]),
    "nehru_jacket": ("Nehru jacket", ["nehru jacket", "bandi", "modi jacket"]),
    "blazer":      ("Blazer",       ["blazer", "suit jacket", "sport coat"]),
    "jeans":       ("Jeans",        ["jeans", "jean", "denim", "denims"]),
    "trousers":    ("Trousers",     ["trousers", "trouser", "formal trousers", "chinos", "chino", "pants", "slacks"]),
    "track_pants": ("Track pants",  ["track pants", "trackpants", "joggers", "jogger", "sweatpants"]),
    "tracksuit":   ("Tracksuit",    ["tracksuit", "track suit"]),
    "skirt":       ("Skirt",        ["skirt", "midi skirt", "mini skirt", "maxi skirt"]),
    "dress":       ("Dress",        ["dress", "frock", "gown", "floral dress"]),
    "dungaree":    ("Dungaree",     ["dungaree", "dungarees", "overalls"]),
    "kurta":       ("Kurta",        ["kurta", "kurti", "anarkali", "kurta pyjama", "kurta set"]),
    "palazzo":     ("Palazzo",      ["palazzo", "palazzo set", "palazzos"]),
    "lehenga":     ("Lehenga",      ["lehenga", "lehnga", "lehanga", "ghagra", "chaniya choli"]),
    "sherwani":    ("Sherwani",     ["sherwani", "achkan"]),
    "sneakers":    ("Sneakers",     ["sneakers", "sneaker", "trainers", "casual shoes", "air max"]),
    "running_shoes": ("Running shoes", ["running shoes", "running shoe", "sports shoes", "running"]),
    "loafers":     ("Loafers",      ["loafers", "loafer", "moccasins", "slip-ons", "slip ons"]),
    "backpack":    ("Backpack",     ["backpack", "rucksack", "bag", "school bag", "laptop bag"]),
}

# Broad words that mean a *group* of types.
TYPE_GROUPS: Dict[str, List[str]] = {
    "tops": ["tshirt", "shirt", "jersey", "hoodie", "sweater", "kurta"],
    "top": ["tshirt", "shirt", "jersey", "hoodie", "sweater", "kurta"],
    "bottoms": ["jeans", "trousers", "track_pants", "skirt", "palazzo"],
    "bottom wear": ["jeans", "trousers", "track_pants", "skirt", "palazzo"],
    "shoes": ["sneakers", "running_shoes", "loafers"],
    "footwear": ["sneakers", "running_shoes", "loafers"],
    "outerwear": ["jacket", "blazer", "nehru_jacket", "hoodie", "sweater"],
    "winterwear": ["jacket", "sweater", "hoodie"],
    "winter wear": ["jacket", "sweater", "hoodie"],
    "ethnic": ["kurta", "sherwani", "lehenga", "palazzo", "nehru_jacket"],
    "ethnic wear": ["kurta", "sherwani", "lehenga", "palazzo", "nehru_jacket"],
    "traditional": ["kurta", "sherwani", "lehenga", "palazzo", "nehru_jacket"],
    "sportswear": ["jersey", "track_pants", "tracksuit", "running_shoes"],
    "activewear": ["jersey", "track_pants", "tracksuit", "running_shoes"],
}

# Shown as "you might also like" only when the exact type has no stock left.
RELATED_TYPES: Dict[str, List[str]] = {
    "tshirt": ["jersey", "shirt"], "jersey": ["tshirt"], "shirt": ["tshirt"],
    "jeans": ["trousers"], "trousers": ["jeans", "track_pants"], "track_pants": ["trousers", "tracksuit"],
    "hoodie": ["sweater", "jacket"], "sweater": ["hoodie"], "jacket": ["blazer", "hoodie"],
    "sneakers": ["running_shoes"], "running_shoes": ["sneakers"], "dress": ["skirt", "kurta"],
    "kurta": ["palazzo"], "lehenga": ["kurta"], "sherwani": ["kurta", "nehru_jacket"],
}

# ── Colours ──────────────────────────────────────────────────────────────────
# canonical colour -> synonyms; also an sRGB anchor used by the image matcher.
COLORS: Dict[str, Tuple[Tuple[int, int, int], List[str]]] = {
    "red":    ((200, 30, 40),   ["red", "maroon", "crimson", "scarlet", "burgundy", "wine", "cherry", "rust red"]),
    "blue":   ((40, 80, 180),   ["blue", "navy", "navy blue", "royal blue", "sky blue", "indigo", "denim blue", "teal blue", "cobalt"]),
    "green":  ((40, 140, 70),   ["green", "olive", "mint", "emerald", "khaki green", "sage", "bottle green"]),
    "black":  ((20, 20, 20),    ["black", "jet black", "charcoal black", "onyx"]),
    "white":  ((240, 240, 240), ["white", "off white", "off-white", "ivory", "cream"]),
    "grey":   ((130, 130, 130), ["grey", "gray", "charcoal", "ash", "silver", "slate"]),
    "yellow": ((235, 200, 40),  ["yellow", "mustard", "lemon", "golden", "gold"]),
    "pink":   ((235, 120, 170), ["pink", "rose", "blush", "peach", "fuchsia", "magenta"]),
    "orange": ((240, 130, 30),  ["orange", "rust", "coral", "tangerine", "saffron"]),
    "purple": ((120, 60, 150),  ["purple", "violet", "lavender", "lilac", "plum", "mauve"]),
    "brown":  ((120, 75, 40),   ["brown", "tan", "beige", "camel", "chocolate", "coffee", "khaki"]),
}

GENDERS: Dict[str, List[str]] = {
    "men": ["men", "mens", "men's", "man", "male", "boys", "gents", "him", "guy", "guys"],
    "women": ["women", "womens", "women's", "woman", "female", "girls", "ladies", "her", "lady"],
    "kids": ["kids", "kid", "children", "child", "boy", "girl", "toddler", "baby"],
}

SIZES = ["xxxl", "xxl", "xl", "xs", "s", "m", "l"]
_SIZE_WORDS = {"small": "s", "medium": "m", "large": "l", "extra large": "xl", "extra small": "xs"}

STOPWORDS = set("""a an the some any me my i im i'm for to of in on with and or show find get give want need
looking look search searching please pls can could would like something items item products product stuff
only just also more other options option them those these one ones that this what which under below above over
less than between and price budget rs inr rupees ₹ size colour color in colored coloured shade help us we
you your yours wear wearing buy buying shop shopping available have has got see let lets let's""".split())

_ZS_THRESHOLD = 0.62           # zero-shot acceptance (cosine); below this we refuse to guess
_FUZZY_THRESHOLD = 0.84        # difflib ratio for typo matching


def _norm(s: str) -> str:
    s = (s or "").lower().replace("’", "'")
    s = re.sub(r"(\d),(?=\d{2,3}\b)", r"\1", s)        # 2,000 -> 2000 (before punctuation is stripped)
    s = re.sub(r"[^a-z0-9₹'\- ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _build_index(table: Dict[str, Tuple]) -> List[Tuple[str, str]]:
    """(phrase, canonical) sorted longest phrase first so 'polo t-shirt' beats 'shirt'."""
    out = []
    for canon, (_, syns) in table.items():
        for p in syns:
            out.append((_norm(p), canon))
            out.append((_norm(p).replace("-", " "), canon))
            out.append((_norm(p).replace("-", ""), canon))
    return sorted(set(out), key=lambda x: -len(x[0]))


_TYPE_INDEX = _build_index(PRODUCT_TYPES)
_COLOR_INDEX = _build_index(COLORS)
_GROUP_INDEX = sorted(((_norm(k), k) for k in TYPE_GROUPS), key=lambda x: -len(x[0]))


def _find_phrases(text: str, index: List[Tuple[str, str]]) -> Tuple[List[str], str]:
    """Return canonicals found (in order) and the text with matches blanked out."""
    found: List[str] = []
    padded = f" {text} "
    for phrase, canon in index:
        pat = f" {phrase} "
        # plural 's' tolerance for single words: "jerseys", "hoodies"
        variants = [pat] + ([f" {phrase}s ", f" {phrase}es "] if " " not in phrase else [])
        for v in variants:
            while v in padded:
                if canon not in found:
                    found.append(canon)
                padded = padded.replace(v, " " + "_" * (len(v) - 2) + " ", 1)
    return found, padded.strip()


def _singular(w: str) -> str:
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("es") and len(w) > 4 and w[-3] in "sxz":
        return w[:-2]
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        return w[:-1]
    return w


def _fuzzy_type(word: str) -> Optional[str]:
    w = _singular(word)
    best, score = None, 0.0
    for phrase, canon in _TYPE_INDEX:
        if " " in phrase or len(phrase) < 3:
            continue
        r = difflib.SequenceMatcher(None, w, phrase).ratio()
        if r > score:
            best, score = canon, r
    return best if score >= _FUZZY_THRESHOLD else None


def _fuzzy_color(word: str) -> Optional[str]:
    best, score = None, 0.0
    for phrase, canon in _COLOR_INDEX:
        if " " in phrase or len(phrase) < 3:
            continue
        r = difflib.SequenceMatcher(None, word, phrase).ratio()
        if r > score:
            best, score = canon, r
    return best if score >= 0.86 else None


# ── Zero-shot fallback (embedding prototypes) ────────────────────────────────
_proto_lock = threading.Lock()
_protos: Optional[Dict[str, List[float]]] = None


def _cos(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


def _type_prototypes() -> Dict[str, List[float]]:
    global _protos
    if _protos is None:
        with _proto_lock:
            if _protos is None:
                from app.services.embedding_service import generate_text_embeddings_batch
                canons = list(PRODUCT_TYPES)
                descs = [f"{PRODUCT_TYPES[c][0]}: " + ", ".join(PRODUCT_TYPES[c][1][:5]) for c in canons]
                vecs = generate_text_embeddings_batch(descs, task_type="search_document")
                protos = {c: v for c, v in zip(canons, vecs) if any(v)}
                if protos:            # don't cache a failed (all-zero) build
                    _protos = protos
                return protos
    return _protos or {}


def zero_shot_type(phrase: str) -> Tuple[Optional[str], float]:
    """Nearest product-type prototype for an unknown phrase; (None, score) if not confident."""
    try:
        from app.services.embedding_service import generate_text_embedding
        protos = _type_prototypes()
        if not protos:
            return None, 0.0
        q = generate_text_embedding(phrase, task_type="search_query")
        if not any(q):
            return None, 0.0
        best = max(((c, _cos(q, v)) for c, v in protos.items()), key=lambda x: x[1])
        return (best[0], best[1]) if best[1] >= _ZS_THRESHOLD else (None, best[1])
    except Exception:
        return None, 0.0


# ── Query parsing ────────────────────────────────────────────────────────────
@dataclass
class QueryFilters:
    types: List[str] = field(default_factory=list)       # canonical product types (OR)
    colors: List[str] = field(default_factory=list)      # canonical colours (OR)
    exclude_colors: List[str] = field(default_factory=list)
    gender: Optional[str] = None                         # men | women | kids
    sizes: List[str] = field(default_factory=list)
    brands: List[str] = field(default_factory=list)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    keywords: List[str] = field(default_factory=list)    # leftover words, used only for ranking
    type_source: Optional[str] = None                    # lexicon | fuzzy | zero-shot | agent
    notes: List[str] = field(default_factory=list)

    def has_constraints(self) -> bool:
        return bool(self.types or self.colors or self.gender or self.sizes or self.brands
                    or self.min_price or self.max_price or self.exclude_colors)

    def describe(self) -> str:
        parts = []
        if self.colors:
            parts.append("/".join(self.colors))
        if self.types:
            parts.append(" or ".join(type_label(t) for t in self.types))
        if self.gender:
            parts.append(f"for {self.gender}")
        if self.sizes:
            parts.append("size " + "/".join(s.upper() for s in self.sizes))
        if self.brands:
            parts.append("by " + "/".join(self.brands))
        if self.min_price and self.max_price:
            parts.append(f"₹{self.min_price:.0f}-₹{self.max_price:.0f}")
        elif self.max_price:
            parts.append(f"under ₹{self.max_price:.0f}")
        elif self.min_price:
            parts.append(f"over ₹{self.min_price:.0f}")
        if self.exclude_colors:
            parts.append("not " + "/".join(self.exclude_colors))
        return " ".join(parts) or "anything"

    def to_dict(self) -> dict:
        return asdict(self)


def type_label(canon: str) -> str:
    return PRODUCT_TYPES.get(canon, (canon.replace("_", " ").title(), []))[0]


def _parse_price(text: str, f: QueryFilters) -> str:
    num = r"(?:₹|rs\.?|inr)?\s*(\d[\d,]*(?:\.\d+)?)\s*(k)?"

    def val(m, gi=1):
        v = float(m.group(gi).replace(",", ""))
        return v * 1000 if m.group(gi + 1) else v

    m = re.search(rf"between\s+{num}\s+(?:and|to|-)\s+{num}", text)
    if m:
        f.min_price, f.max_price = val(m, 1), val(m, 3)
        return text.replace(m.group(0), " ")
    m = re.search(rf"{num}\s*(?:-|to)\s*{num}", text)
    if m and ("₹" in m.group(0) or "rs" in m.group(0) or val(m, 1) >= 100):
        f.min_price, f.max_price = val(m, 1), val(m, 3)
        return text.replace(m.group(0), " ")
    m = re.search(rf"(?:under|below|less than|upto|up to|within|max|maximum|cheaper than|<)\s*{num}", text)
    if m:
        f.max_price = val(m)
        text = text.replace(m.group(0), " ")
    m = re.search(rf"(?:above|over|more than|at least|min|minimum|>)\s*{num}", text)
    if m:
        f.min_price = val(m)
        text = text.replace(m.group(0), " ")
    return text


def _parse_size(text: str, f: QueryFilters) -> str:
    for word, s in _SIZE_WORDS.items():
        m = re.search(rf"\bsize\s+{word}\b|\b{word}\s+size\b", text)
        if m:
            f.sizes.append(s)
            text = text.replace(m.group(0), " ")
    for m in re.finditer(r"\b(?:size\s+)(xxxl|xxl|xl|xs|s|m|l|\d{1,2})\b|\b(xxxl|xxl|xl|xs)\b", text):
        s = (m.group(1) or m.group(2)).lower()
        if s not in f.sizes:
            f.sizes.append(s)
    text = re.sub(r"\bsize\s+(xxxl|xxl|xl|xs|s|m|l|\d{1,2})\b|\b(xxxl|xxl|xl|xs)\b", " ", text)
    return text


def parse_query(query: str, known_brands: Optional[List[str]] = None, allow_zero_shot: bool = True) -> QueryFilters:
    f = QueryFilters()
    text = _norm(query)

    text = _parse_price(text, f)
    text = _parse_size(text, f)

    # negated colours: "not black", "no white", "except red"
    for m in re.finditer(r"\b(?:not|no|except|without|avoid)\s+([a-z\- ]+?)(?=\b(?:and|or|,|$)|\s(?:t-?shirts?|jeans|shirts?|$))", text):
        cols, _ = _find_phrases(_norm(m.group(1)), _COLOR_INDEX)
        f.exclude_colors += [c for c in cols if c not in f.exclude_colors]
    text = re.sub(r"\b(?:not|no|except|without|avoid)\s+(" + "|".join(re.escape(p) for p, _ in _COLOR_INDEX) + r")\b", " ", text)

    # specific types first ("running shoes"), then broad groups ("shoes", "tops")
    # only if no specific type was named
    types, text = _find_phrases(text, _TYPE_INDEX)
    for t in types:
        if t not in f.types:
            f.types.append(t)
    groups, text = _find_phrases(text, [(p, k) for p, k in _GROUP_INDEX])
    if not f.types:
        for g in groups:
            for t in TYPE_GROUPS[g]:
                if t not in f.types:
                    f.types.append(t)
    if f.types:
        f.type_source = "lexicon"

    cols, text = _find_phrases(text, _COLOR_INDEX)
    f.colors = [c for c in cols if c not in f.exclude_colors]

    for g, syns in GENDERS.items():
        for s in sorted(syns, key=len, reverse=True):
            if re.search(rf"(?<![a-z']){re.escape(s)}(?![a-z'])", text):
                f.gender = f.gender or g
                text = re.sub(rf"(?<![a-z']){re.escape(s)}(?![a-z'])", " ", text)

    if known_brands:
        for b in known_brands:
            nb = _norm(b)
            if nb and re.search(rf"(?<![a-z]){re.escape(nb)}(?![a-z])", text):
                f.brands.append(b)
                text = text.replace(nb, " ")

    leftovers = [w for w in re.split(r"[\s\-]+", text.replace("_", " ")) if w and w not in STOPWORDS and not w.isdigit()]
    unresolved = []
    for w in leftovers:
        if not f.types:
            t = _fuzzy_type(w)
            if t:
                f.types.append(t)
                f.type_source = "fuzzy"
                f.notes.append(f"read '{w}' as {type_label(t)}")
                continue
        if not f.colors:
            c = _fuzzy_color(w)
            if c:
                f.colors.append(c)
                continue
        unresolved.append(w)
    f.keywords = unresolved

    if not f.types and unresolved and allow_zero_shot:
        phrase = " ".join(unresolved)
        t, score = zero_shot_type(phrase)
        if t:
            f.types.append(t)
            f.type_source = "zero-shot"
            f.notes.append(f"'{phrase}' looks like {type_label(t)} (similarity {score:.2f})")
    return f


def normalize_type(value: Optional[str]) -> List[str]:
    """Agent-supplied product type -> canonical types (lexicon, group, fuzzy, then zero-shot)."""
    if not value:
        return []
    v = _norm(value)
    if v in TYPE_GROUPS:
        return list(TYPE_GROUPS[v])
    found, _ = _find_phrases(v, _TYPE_INDEX)
    if found:
        return found
    t = _fuzzy_type(v.replace(" ", ""))
    if t:
        return [t]
    t, _ = zero_shot_type(v)
    return [t] if t else []


def normalize_color(value: Optional[str]) -> List[str]:
    if not value:
        return []
    found, _ = _find_phrases(_norm(value), _COLOR_INDEX)
    if found:
        return found
    c = _fuzzy_color(_norm(value))
    return [c] if c else []


def normalize_gender(value: Optional[str]) -> Optional[str]:
    v = _norm(value or "")
    if not v or v == "unisex":
        return None
    for g, syns in GENDERS.items():
        if v == g or v in syns:
            return g
    return None


# ── Catalog-side classification ──────────────────────────────────────────────
def classify_product(name: str, category: Optional[str] = None, description: Optional[str] = None) -> Optional[str]:
    """Product type from its own name first, then category, then description."""
    for source in (name, category, description):
        if not source:
            continue
        # Head noun wins: in "Palazzo Kurti" or "Polo T-Shirt" the last matched
        # phrase is what the item is. Longest phrase wins ties at the same end.
        text = f" {_norm(source)} "
        best, best_key = None, None
        for phrase, canon in _TYPE_INDEX:
            for v in (f" {phrase} ", f" {phrase}s "):
                i = text.rfind(v)
                if i >= 0:
                    key = (i + len(v), len(phrase))
                    if best_key is None or key > best_key:
                        best, best_key = canon, key
        if best:
            return best
    cat = _norm(category or "")
    if cat in ("shoes", "footwear"):
        return "sneakers"
    return None


def product_gender(raw: Optional[str]) -> str:
    v = _norm(raw or "")
    if v in ("male", "men", "man", "mens", "boys"):
        return "men"
    if v in ("female", "women", "woman", "womens", "girls", "ladies"):
        return "women"
    if v in ("kids", "kid", "children", "boy", "girl"):
        return "kids"
    return "unisex"


def color_of(raw: Optional[str]) -> Optional[str]:
    found = normalize_color(raw)
    return found[0] if found else None


_type_cache: Dict[str, Tuple[float, Optional[str]]] = {}


def product_type_cached(product_id: str, name: str, category: Optional[str], description: Optional[str]) -> Optional[str]:
    hit = _type_cache.get(product_id)
    if hit and time.monotonic() - hit[0] < 600:
        return hit[1]
    t = classify_product(name, category, description)
    if t is None:
        z, _ = zero_shot_type(f"{name} {category or ''}".strip())
        t = z
    _type_cache[product_id] = (time.monotonic(), t)
    return t

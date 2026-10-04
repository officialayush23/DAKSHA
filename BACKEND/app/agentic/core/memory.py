"""
Per-agent memory.

Each agent owns a private namespace (domain, agent, principal). The discovery
agent remembers that a shopper hates polyester; the post-purchase agent
remembers that the last return was approved late. Neither can read the
other's notes. What *everyone* needs to know (cart, orders, tier ...) lives in
the unified context instead, which is rebuilt from the system of record on
every turn.

Recall is cheap on purpose: no embedding call on the hot path. We pull the
newest rows for the namespace and rank them by salience, recency and keyword
overlap with the current objective.
"""
from __future__ import annotations

import json
import math
import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "to", "for", "of", "and", "or", "in", "on", "my", "me", "i", "is", "it", "with", "user", "customer"}


def _terms(text: str) -> set:
    return {w for w in _WORD.findall((text or "").lower()) if w not in _STOP and len(w) > 2}


@dataclass
class MemoryItem:
    content: str
    kind: str = "episodic"            # episodic | semantic | preference
    salience: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta: Dict[str, Any] = field(default_factory=dict)


def rank(items: List[MemoryItem], query: str, k: int = 5, half_life_days: float = 14.0) -> List[MemoryItem]:
    q = _terms(query)
    now = datetime.now(timezone.utc)
    scored = []
    for it in items:
        age_days = max(0.0, (now - it.created_at).total_seconds() / 86400)
        recency = math.exp(-age_days * math.log(2) / half_life_days)
        t = _terms(it.content)
        overlap = len(q & t) / len(q | t) if (q and t) else 0.0
        bonus = 0.15 if it.kind in ("preference", "semantic") else 0.0
        scored.append((0.35 * it.salience + 0.30 * recency + 0.35 * overlap + bonus, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:k]]


class MemoryStore:
    def recall(self, domain: str, agent: str, principal: Optional[str], query: str, k: int = 5) -> List[MemoryItem]:
        raise NotImplementedError

    def write(self, domain: str, agent: str, principal: Optional[str], item: MemoryItem) -> None:
        raise NotImplementedError


class InMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._rows: Dict[tuple, List[MemoryItem]] = {}
        self._lock = threading.Lock()

    def recall(self, domain, agent, principal, query, k=5):
        with self._lock:
            rows = list(self._rows.get((domain, agent, principal), []))[-50:]
        return rank(rows, query, k)

    def write(self, domain, agent, principal, item):
        with self._lock:
            self._rows.setdefault((domain, agent, principal), []).append(item)


class SqlMemoryStore(MemoryStore):
    """Backed by the agent_memories table (migrations/v7_agentic_core.sql)."""

    def __init__(self, session_factory=None) -> None:
        if session_factory is None:
            from app.core.database import SessionLocal
            session_factory = SessionLocal
        self._sf = session_factory

    def recall(self, domain, agent, principal, query, k=5):
        if not principal:
            return []
        from sqlalchemy import text
        with self._sf() as db:
            rows = db.execute(text("""
                SELECT content, kind, salience, created_at, meta
                FROM agent_memories
                WHERE domain = :d AND agent = :a AND user_id = :u
                ORDER BY created_at DESC LIMIT 50
            """), {"d": domain, "a": agent, "u": principal}).fetchall()
        items = [MemoryItem(r.content, r.kind, float(r.salience or 0.5),
                            r.created_at if r.created_at.tzinfo else r.created_at.replace(tzinfo=timezone.utc),
                            r.meta or {}) for r in rows]
        return rank(items, query, k)

    def write(self, domain, agent, principal, item):
        if not principal:
            return
        from sqlalchemy import text
        with self._sf() as db:
            db.execute(text("""
                INSERT INTO agent_memories (id, domain, agent, user_id, kind, content, salience, meta)
                VALUES (:id, :d, :a, :u, :k, :c, :s, CAST(:m AS jsonb))
            """), {"id": str(uuid.uuid4()), "d": domain, "a": agent, "u": principal, "k": item.kind,
                   "c": item.content[:1000], "s": item.salience, "m": json.dumps(item.meta, default=str)})
            db.commit()

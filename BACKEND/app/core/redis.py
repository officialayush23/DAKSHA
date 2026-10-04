# app/core/redis.py
"""
Optional Redis.

DAKSHA works without Redis. When REDIS_URL is missing or the server can't be
reached, `redis_client` transparently falls back to a small in-process TTL
store, so caches still work on a single instance. `redis_available()` tells
callers (Celery dispatch, pub/sub) whether the real server is up.
"""
import logging
import threading
import time

from app.core.config import settings

log = logging.getLogger("daksha.redis")


class _LocalTTLStore:
    """Tiny subset of the redis-py API used by the app."""

    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def _alive(self, key):
        item = self._data.get(key)
        if not item:
            return None
        value, exp = item
        if exp and exp < time.monotonic():
            self._data.pop(key, None)
            return None
        return value

    def get(self, key):
        with self._lock:
            return self._alive(key)

    def set(self, key, value, ex=None):
        with self._lock:
            self._data[key] = (str(value), time.monotonic() + ex if ex else None)
        return True

    def setex(self, key, ttl, value):
        return self.set(key, value, ex=ttl)

    def delete(self, *keys):
        with self._lock:
            return sum(1 for k in keys if self._data.pop(k, None) is not None)

    def incr(self, key):
        with self._lock:
            v = int(self._alive(key) or 0) + 1
            exp = self._data.get(key, (None, None))[1]
            self._data[key] = (str(v), exp)
            return v

    def expire(self, key, ttl):
        with self._lock:
            if key in self._data:
                self._data[key] = (self._data[key][0], time.monotonic() + ttl)
        return True

    def ping(self):
        return True


_real = None
_checked_at = 0.0
_ok = False
_local = _LocalTTLStore()


def redis_available(recheck_s: float = 300.0) -> bool:
    """True if the configured Redis answers PING. Cached for `recheck_s`."""
    global _real, _checked_at, _ok
    if not settings.REDIS_URL:
        return False
    now = time.monotonic()
    if now - _checked_at < recheck_s:
        return _ok
    _checked_at = now
    try:
        import redis
        if _real is None:
            _real = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True,
                                         socket_connect_timeout=2, socket_timeout=2)
        _ok = bool(_real.ping())
    except Exception as e:
        if _ok or _checked_at == now:
            log.warning("Redis unavailable, using in-process fallback: %s", str(e)[:120])
        _ok = False
    return _ok


class _Facade:
    def __getattr__(self, name):
        target = _real if redis_available() else _local
        return getattr(target, name)


redis_client = _Facade()

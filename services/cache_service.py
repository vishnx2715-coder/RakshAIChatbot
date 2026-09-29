"""
services/cache_service.py — Redis-backed cache for RAKSHA.

Public API:
    cache_get(key)              → value (deserialized) or None
    cache_set(key, value, ttl)  → None
    cached(prefix, ttl)         → decorator

Key namespace: "raksha:"

Redis down behaviour:
    - ConnectionError / TimeoutError are caught and logged.
    - cache_get returns None (callers fall back to direct API fetch).
    - cache_set silently no-ops.
    - A 30-second cooldown prevents hammering a dead Redis on every request.

Stampede guard:
    lock_acquire(key, ttl) / lock_release(key) use Redis SET NX EX.
    Used by RSS and GDACS refresh loops so only one worker fetches at a time.

Never cache:
    - Per-user or session data
    - Auth responses

TTLs configured in Config:
    RSS_TTL_SECONDS         300 s
    GDACS_TTL_SECONDS       600 s
    WEATHER_TTL_SECONDS     600 s
    INDIA_RISK_TTL_SECONDS  300 s
    SHELTERS_TTL_SECONDS   3600 s
"""

import functools
import json
import logging
import time
from typing import Any, Optional

from config import Config

logger = logging.getLogger(__name__)

_NAMESPACE = "raksha:"
_LOCK_SUFFIX = ":lock"
_COOLDOWN_SECONDS = 30  # don't retry Redis for this long after a failure


# ── Connection management ─────────────────────────────────────

_redis_client = None          # lazy-init on first use
_redis_down_since: float = 0.0  # monotonic timestamp of last failure; 0 = healthy


def _get_client():
    """
    Return a Redis client, or None if Redis is unavailable / in cooldown.
    Initialises the client lazily on first call.
    """
    global _redis_client, _redis_down_since

    # Cooldown: don't attempt Redis for _COOLDOWN_SECONDS after a failure
    if _redis_down_since and (time.monotonic() - _redis_down_since) < _COOLDOWN_SECONDS:
        return None

    if _redis_client is None:
        if not Config.REDIS_URL:
            return None
        try:
            import redis
            _redis_client = redis.from_url(
                Config.REDIS_URL,
                decode_responses=True,   # always get str back
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Warm-test the connection
            _redis_client.ping()
            _redis_down_since = 0.0
            logger.info("Redis connected: %s", Config.REDIS_URL.split("@")[-1])
        except Exception as e:
            logger.warning("Redis unavailable (%s) — caching disabled, falling back to direct API", e)
            _redis_client = None
            _redis_down_since = time.monotonic()
            return None

    return _redis_client


def _mark_down(exc: Exception) -> None:
    """Record a Redis failure and start the cooldown timer."""
    global _redis_client, _redis_down_since
    logger.warning("Redis error (%s) — entering %ds cooldown", exc, _COOLDOWN_SECONDS)
    _redis_client    = None
    _redis_down_since = time.monotonic()


# ── Core API ─────────────────────────────────────────────────

def cache_get(key: str) -> Optional[Any]:
    """
    Return the cached value for key, or None on miss / Redis down.
    Keys are automatically namespaced with "raksha:".
    Values are JSON-serialized on write; deserialized on read.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(_NAMESPACE + key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        _mark_down(e)
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """
    Store value under key with TTL (seconds).
    Silently no-ops if Redis is down.
    """
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(_NAMESPACE + key, ttl, json.dumps(value, ensure_ascii=False))
    except Exception as e:
        _mark_down(e)


def cached(prefix: str, ttl: int = 300):
    """
    Decorator: cache the return value of the wrapped function.

    The full cache key is  "{prefix}:{args_repr}".
    Use prefix to distinguish different callers with the same args.

    Example:
        @cached("gdacs", ttl=600)
        def fetch_gdacs_events():
            ...

    Redis down → function is called directly every time (no error).
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Build a deterministic key from positional args
            key = prefix + ":" + ":".join(str(a) for a in args)
            hit = cache_get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            if result is not None:
                cache_set(key, result, ttl)
            return result
        return wrapper
    return decorator


# ── Stampede guard ────────────────────────────────────────────

def lock_acquire(key: str, ttl: int = 30) -> bool:
    """
    Try to acquire a distributed lock (SET NX EX).
    Returns True if the lock was acquired, False if already held.
    Falls back to True (proceed) if Redis is down — single worker is fine.
    """
    client = _get_client()
    if client is None:
        return True   # no Redis → no contention, always proceed
    try:
        lock_key = _NAMESPACE + key + _LOCK_SUFFIX
        result = client.set(lock_key, "1", nx=True, ex=ttl)
        return result is True
    except Exception as e:
        _mark_down(e)
        return True   # Redis error → assume acquired, proceed with fetch


def lock_release(key: str) -> None:
    """Release a distributed lock. Best-effort; does not raise."""
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(_NAMESPACE + key + _LOCK_SUFFIX)
    except Exception as e:
        _mark_down(e)

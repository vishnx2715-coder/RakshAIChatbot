"""
services/cache_service.py — Caching layer for RAKSHA.

Phase 4 stub: passes through to direct fetch (no caching).
Phase 6 will replace this with Redis-backed implementation.

Public API (stable — blueprints import these):
  cache_get(key) → value or None
  cache_set(key, value, ttl) → None
  cached(prefix, ttl) → decorator
"""

import functools
import json
import logging

logger = logging.getLogger(__name__)

# ── Phase 4 stub — no-op cache ────────────────────────────────

def cache_get(key: str):
    """Return None (cache miss) — stub for Phase 6."""
    return None


def cache_set(key: str, value, ttl: int = 300) -> None:
    """No-op — stub for Phase 6."""
    pass


def cached(prefix: str, ttl: int = 300):
    """
    Decorator stub — calls the wrapped function directly.
    Phase 6 will add Redis get/set around the call.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper
    return decorator

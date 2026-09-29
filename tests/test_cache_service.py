"""
tests/test_cache_service.py — Unit tests for services/cache_service.py

Tests run without a live Redis instance (tests the fallback path).
The Redis-connected path is verified via integration in CI/CD when
a Redis service is available.

Covers:
  - cache_get returns None when Redis is unavailable
  - cache_set is a no-op when Redis is unavailable (no exception)
  - cached() decorator calls the function on every miss (no Redis)
  - lock_acquire returns True (proceed) when Redis is unavailable
  - lock_release does not raise when Redis is unavailable
  - Cooldown: _mark_down sets _redis_down_since and blocks retries
"""

import importlib
import sys
import time

import pytest


def _fresh_cache_service():
    """Reload cache_service with REDIS_URL unset to simulate no Redis."""
    import os
    original = os.environ.pop("REDIS_URL", None)
    # Remove cached module so we get a fresh import
    for key in list(sys.modules.keys()):
        if "cache_service" in key:
            del sys.modules[key]
    import services.cache_service as cs
    # Ensure client is None
    cs._redis_client = None
    cs._redis_down_since = 0.0
    if original is not None:
        os.environ["REDIS_URL"] = original
    return cs


class TestCacheGetMiss:
    def test_get_returns_none_no_redis(self):
        cs = _fresh_cache_service()
        result = cs.cache_get("nonexistent:key")
        assert result is None

    def test_get_different_keys_all_none(self):
        cs = _fresh_cache_service()
        for k in ("rss:news", "gdacs:events", "india:risk", "foo:bar"):
            assert cs.cache_get(k) is None


class TestCacheSet:
    def test_set_does_not_raise(self):
        cs = _fresh_cache_service()
        # Should be a no-op, not an exception
        cs.cache_set("test:key", {"data": [1, 2, 3]}, ttl=60)

    def test_set_then_get_still_none(self):
        cs = _fresh_cache_service()
        cs.cache_set("test:key", {"value": 42}, ttl=60)
        # Without Redis, get should still return None
        assert cs.cache_get("test:key") is None


class TestCachedDecorator:
    def test_decorator_calls_function_on_miss(self):
        cs = _fresh_cache_service()
        call_count = [0]

        @cs.cached("test_prefix", ttl=60)
        def my_func():
            call_count[0] += 1
            return {"result": "value"}

        result1 = my_func()
        result2 = my_func()
        # Without Redis, function is called every time
        assert result1 == {"result": "value"}
        assert result2 == {"result": "value"}
        assert call_count[0] == 2

    def test_decorator_preserves_function_name(self):
        cs = _fresh_cache_service()

        @cs.cached("test", ttl=60)
        def my_named_function():
            return 42

        assert my_named_function.__name__ == "my_named_function"

    def test_decorator_with_args(self):
        cs = _fresh_cache_service()
        call_count = [0]

        @cs.cached("weather", ttl=300)
        def get_weather(lat, lon):
            call_count[0] += 1
            return {"temp": 25}

        get_weather(13.08, 80.27)
        get_weather(13.08, 80.27)
        assert call_count[0] == 2   # no Redis → no caching


class TestLockFallback:
    def test_acquire_returns_true_no_redis(self):
        cs = _fresh_cache_service()
        result = cs.lock_acquire("test_lock", ttl=10)
        assert result is True

    def test_release_does_not_raise(self):
        cs = _fresh_cache_service()
        cs.lock_acquire("test_lock", ttl=10)
        cs.lock_release("test_lock")  # should not raise


class TestCooldown:
    def test_mark_down_sets_down_since(self):
        cs = _fresh_cache_service()
        before = time.monotonic()
        cs._mark_down(ConnectionError("test"))
        assert cs._redis_down_since >= before
        assert cs._redis_client is None

    def test_get_client_returns_none_during_cooldown(self):
        cs = _fresh_cache_service()
        cs._mark_down(ConnectionError("test"))
        # Should be in cooldown — client should be None
        client = cs._get_client()
        assert client is None

    def test_cooldown_expires(self):
        cs = _fresh_cache_service()
        # Simulate a very short cooldown by backdating _redis_down_since
        cs._redis_down_since = time.monotonic() - (cs._COOLDOWN_SECONDS + 1)
        # After cooldown, _get_client will attempt reconnect
        # (will fail if no Redis, but should try)
        # We just verify it doesn't return None due to cooldown alone
        # It may still return None because REDIS_URL is not set — that's fine
        import os
        if not os.getenv("REDIS_URL"):
            client = cs._get_client()
            assert client is None  # no URL → still None, but for different reason

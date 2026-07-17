import time
from collections import defaultdict

from app.core.logger import logger


class FixedWindowLimiter:
    """In-process fixed window rate limiter.

    Only correct for a single worker/process — each replica keeps its own
    counters. Kept around for tests (see tests/conftest.py) and for local
    single-worker dev. Real deployments should use RedisFixedWindowLimiter.
    """

    def __init__(self, requests: int, window_seconds: int):
        self.requests = requests
        self.window = window_seconds
        self.counters: dict = defaultdict(lambda: {"count": 0, "window_start": 0})

    async def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = int(now / self.window) * self.window

        counter = self.counters[key]

        if counter["window_start"] != window_start:
            counter["count"] = 0
            counter["window_start"] = window_start

        if counter["count"] >= self.requests:
            return False

        counter["count"] += 1
        return True

    async def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window"""
        now = time.time()
        window_start = int(now / self.window) * self.window

        counter = self.counters[key]

        if counter["window_start"] != window_start:
            return self.requests

        return max(0, self.requests - counter["count"])

    async def reset(self) -> None:
        self.counters.clear()


class RedisFixedWindowLimiter:
    """Fixed-window rate limiter backed by Redis (INCR + EXPIRE), correct
    across multiple worker processes/replicas sharing the same Redis.

    Fails open: if Redis is unreachable, requests are allowed through rather
    than the whole API going down because the rate limiter's dependency is
    unavailable. Failures are logged so the outage is still visible.

    A fresh client is created per call rather than cached — `redis.asyncio`
    clients bind their connection pool to the event loop active when first
    used, and a cached client breaks with "Event loop is closed" as soon as
    it's reused under a different loop (e.g. pytest-asyncio's per-test
    loops). Constructing `redis.asyncio.Redis(...)` itself does no I/O, so
    this costs nothing beyond the (already-required) connection setup.
    """

    def __init__(self, requests: int, window_seconds: int, redis_client_factory, prefix: str = "ratelimit"):
        self.requests = requests
        self.window = window_seconds
        self._redis_client_factory = redis_client_factory
        self._prefix = prefix

    def _redis_key(self, key: str) -> str:
        window_start = int(time.time() / self.window)
        return f"{self._prefix}:{key}:{window_start}"

    async def is_allowed(self, key: str) -> bool:
        try:
            client = self._redis_client_factory()
            redis_key = self._redis_key(key)
            count = await client.incr(redis_key)
            if count == 1:
                await client.expire(redis_key, self.window)
            return count <= self.requests
        except Exception as exc:
            logger.warning("Rate limiter Redis error, failing open: %s", exc)
            return True

    async def get_remaining(self, key: str) -> int:
        try:
            client = self._redis_client_factory()
            redis_key = self._redis_key(key)
            count = await client.get(redis_key)
            count = int(count) if count is not None else 0
            return max(0, self.requests - count)
        except Exception as exc:
            logger.warning("Rate limiter Redis error, failing open: %s", exc)
            return self.requests

    async def reset(self) -> None:
        """Clear all counters under this limiter's prefix. Real I/O (unlike
        the in-memory limiter's synchronous reset) — used by tests to get
        true isolation between runs against a real Redis."""
        try:
            client = self._redis_client_factory()
            keys = [key async for key in client.scan_iter(match=f"{self._prefix}:*")]
            if keys:
                await client.delete(*keys)
        except Exception as exc:
            logger.warning("Rate limiter Redis error during reset: %s", exc)

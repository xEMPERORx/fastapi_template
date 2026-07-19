import time
import uuid

from app.core.logger import logger


class RedisSlidingWindowLimiter:
    """Sliding-window-log rate limiter backed by a Redis sorted set.

    Unlike a fixed window (which resets sharply on window boundaries and lets
    up to ~2x the limit through if requests cluster around the boundary),
    this records the timestamp of every request as a member of a Redis
    sorted set and, on each check, atomically trims anything older than
    `window` seconds before counting what's left — so the limit always
    applies to a true trailing window, not a fixed bucket. Correct across
    multiple worker processes/replicas sharing the same Redis.

    The trim + add + count + expire happen in a single Redis pipeline
    (MULTI/EXEC) so concurrent requests for the same key can't race past
    each other between the count and the increment, the same guarantee the
    old INCR-based fixed window had.

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
        return f"{self._prefix}:{key}"

    async def is_allowed(self, key: str) -> bool:
        try:
            client = self._redis_client_factory()
            redis_key = self._redis_key(key)
            now = time.time()
            window_start = now - self.window
            member = f"{now}:{uuid.uuid4().hex}"

            pipe = client.pipeline(transaction=True)
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zadd(redis_key, {member: now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, self.window)
            _, _, count, _ = await pipe.execute()

            if count > self.requests:
                # Best-effort: undo our own entry so a rejected request
                # doesn't still count against the window. If this fails,
                # the entry simply expires out of the window on its own in
                # at most `window` seconds — not a correctness issue.
                await client.zrem(redis_key, member)
                return False

            return True
        except Exception as exc:
            logger.warning("Rate limiter Redis error, failing open: %s", exc)
            return True

    async def get_remaining(self, key: str) -> int:
        try:
            client = self._redis_client_factory()
            redis_key = self._redis_key(key)
            window_start = time.time() - self.window
            await client.zremrangebyscore(redis_key, 0, window_start)
            count = await client.zcard(redis_key)
            return max(0, self.requests - count)
        except Exception as exc:
            logger.warning("Rate limiter Redis error, failing open: %s", exc)
            return self.requests

    async def reset(self) -> None:
        """Clear all counters under this limiter's prefix. Real I/O (unlike
        an in-memory limiter's synchronous reset) — used by tests to get
        true isolation between runs against a real Redis."""
        try:
            client = self._redis_client_factory()
            keys = [key async for key in client.scan_iter(match=f"{self._prefix}:*")]
            if keys:
                await client.delete(*keys)
        except Exception as exc:
            logger.warning("Rate limiter Redis error during reset: %s", exc)

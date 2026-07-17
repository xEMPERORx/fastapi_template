"""
Shared rate limiter instances.

Redis-backed so limits are correct across multiple uvicorn/gunicorn workers
and replicas (the old in-process counter was silently wrong under more than
one worker). `limiter` guards every request; `login_limiter` is a stricter,
per-username throttle applied specifically to the login endpoint for
brute-force resistance independent of which IP the attempt comes from.
"""

from app.core.fixed_window_ratelimit import RedisFixedWindowLimiter
from app.database.redis_db import redis_connect

limiter = RedisFixedWindowLimiter(requests=10, window_seconds=60, redis_client_factory=redis_connect)

login_limiter = RedisFixedWindowLimiter(
    requests=5,
    window_seconds=60,
    redis_client_factory=redis_connect,
    prefix="ratelimit:login",
)

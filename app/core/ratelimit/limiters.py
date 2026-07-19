"""
Shared rate limiter instances.

Redis-backed so limits are correct across multiple uvicorn/gunicorn workers
and replicas (an in-process counter would be silently wrong under more than
one worker). `limiter` guards every request; `login_limiter` is a stricter,
per-username throttle applied specifically to the login endpoint for
brute-force resistance independent of which IP the attempt comes from.
"""

from app.core.ratelimit.sliding_window import RedisSlidingWindowLimiter
from app.database.redis_db import redis_connect


# 120/60s (~2 req/s sustained) rather than a lower number — the admin SPA
# fires several parallel requests per page (e.g. a users list + a grants
# fetch), all from one browser tab sharing one IP, so a limit tuned for a
# single public API caller was starving normal interactive use. Still a real
# ceiling against scraping/abuse, just not one a legitimate dashboard session
# trips into within seconds.
limiter = RedisSlidingWindowLimiter(requests=120, window_seconds=60, redis_client_factory=redis_connect)

login_limiter = RedisSlidingWindowLimiter(
    requests=10,
    window_seconds=60,
    redis_client_factory=redis_connect,
    prefix="ratelimit:login",
)

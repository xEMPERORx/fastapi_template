from app.settings import Config
import redis.asyncio as redis
from redis.backoff import NoBackoff
from redis.retry import Retry


def redis_connect():
    return redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=1.0,
        socket_timeout=1.0,
        # redis-py retries connection errors internally by default, which
        # silently multiplies the timeouts above (observed ~8-13s instead of
        # ~1s when Redis is unreachable). Any retry behavior we want happens
        # at the app.core.resilience.recovery layer instead, deliberately, not here.
        retry=Retry(NoBackoff(), 0),
        retry_on_error=[],
    )


def redis_connect_blocking():
    """Like `redis_connect()`, but without a socket read timeout.

    For long-lived blocking calls (`pubsub.listen()`) that are supposed to
    sit idle between rare events — a 1s read timeout there just means the
    connection times out every ~1s whenever nothing has been published
    recently, which is the common case. Kept in a separate client since the
    short `socket_timeout` on `redis_connect()` is intentional everywhere
    else (fast-fail request/response calls).
    """
    return redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=1.0,
        socket_timeout=None,
        retry=Retry(NoBackoff(), 0),
        retry_on_error=[],
    )

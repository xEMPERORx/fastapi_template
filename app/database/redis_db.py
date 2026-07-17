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
        # at the app.core.recovery layer instead, deliberately, not here.
        retry=Retry(NoBackoff(), 0),
        retry_on_error=[],
    )

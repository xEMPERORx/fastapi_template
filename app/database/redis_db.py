from app.settings import Config
import redis.asyncio as redis

def redis_connect():
    return redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=0,
        decode_responses=True
    )

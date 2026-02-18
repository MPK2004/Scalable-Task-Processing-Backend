import redis.asyncio as redis
import os

MAX_RETRIES = 3

async def get_redis():
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6381))
    
    client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

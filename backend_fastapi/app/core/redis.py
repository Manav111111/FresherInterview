import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger("fresherai.redis")

_redis_client: Optional[aioredis.Redis] = None
_local_cache_store: Dict[str, str] = {}


async def get_redis() -> Optional[aioredis.Redis]:
    """Returns an async Redis client instance, or None if unavailable."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        await client.ping()
        _redis_client = client
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.warning(f"Redis not reachable ({e}). Using local in-memory session fallback.")
        _redis_client = None

    return _redis_client


async def set_cache(key: str, value: str, ex: Optional[int] = None) -> None:
    """Sets cache in Redis with in-memory fallback."""
    _local_cache_store[key] = value
    redis_client = await get_redis()
    if redis_client:
        try:
            if ex:
                await redis_client.set(key, value, ex=ex)
            else:
                await redis_client.set(key, value)
        except Exception as e:
            logger.warning(f"Error setting Redis cache key {key}: {e}")


async def get_cache(key: str) -> Optional[str]:
    """Gets cache value from Redis with in-memory fallback."""
    redis_client = await get_redis()
    if redis_client:
        try:
            val = await redis_client.get(key)
            if val is not None:
                return val
        except Exception as e:
            logger.warning(f"Error getting Redis cache key {key}: {e}")

    return _local_cache_store.get(key)


async def delete_cache(key: str) -> None:
    """Deletes cache key from Redis and in-memory store."""
    _local_cache_store.pop(key, None)
    redis_client = await get_redis()
    if redis_client:
        try:
            await redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Error deleting Redis cache key {key}: {e}")


async def close_redis():
    """Closes Redis client connections gracefully."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None
        logger.info("Redis connection closed.")

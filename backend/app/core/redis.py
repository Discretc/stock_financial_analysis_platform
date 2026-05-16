"""
Redis connection pool and async client helpers.
Provides a singleton async Redis connection for use across the application.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings


# ---------------------------------------------------------------------------
# Connection pool (created once at startup)
# ---------------------------------------------------------------------------

_redis_pool: Redis | None = None


async def init_redis() -> None:
    """Initialize the Redis connection pool. Call from app lifespan."""
    global _redis_pool
    _redis_pool = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )


async def close_redis() -> None:
    """Close the Redis pool. Call from app lifespan teardown."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


def get_redis() -> Redis:
    """
    Return the active Redis client.
    Raises RuntimeError if pool was not initialized.
    """
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialized. Call init_redis() first.")
    return _redis_pool


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_redis_dep() -> AsyncGenerator[Redis, None]:
    """FastAPI dependency that yields the shared Redis client."""
    yield get_redis()


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

async def cache_get(key: str) -> Any | None:
    """Retrieve a JSON-serialized value from Redis. Returns None on miss."""
    redis = get_redis()
    value = await redis.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """
    Store a value in Redis as JSON with the given TTL in seconds.
    Uses SET with EX to guarantee atomicity.
    """
    redis = get_redis()
    serialized = json.dumps(value, default=str)
    await redis.set(key, serialized, ex=ttl)


async def cache_delete(key: str) -> None:
    """Delete a cache entry."""
    redis = get_redis()
    await redis.delete(key)


async def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a glob pattern.
    Uses SCAN to avoid blocking the Redis event loop.
    Returns the number of keys deleted.
    """
    redis = get_redis()
    deleted = 0
    async for key in redis.scan_iter(match=pattern, count=100):
        await redis.delete(key)
        deleted += 1
    return deleted

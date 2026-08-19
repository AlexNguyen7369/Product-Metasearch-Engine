"""
Generic Redis cache layer. Deliberately knows nothing about SerpAPI or any
other provider — it just stores/retrieves JSON by key with a TTL. Swapping
the cache backend or caching a second provider's results later shouldn't
require touching this file.
"""

import json
from typing import Optional

import redis.asyncio as redis

from app.core.config import settings

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Lazily create a single shared Redis connection pool for the app."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def build_cache_key(query: str) -> str:
    """Normalize a search query into a stable cache key."""
    return f"search:{query.strip().lower()}"


async def get_cached(key: str) -> Optional[list]:
    client = get_redis_client()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def set_cached(key: str, value: list, ttl: Optional[int] = None) -> None:
    client = get_redis_client()
    await client.set(key, json.dumps(value), ex=ttl or settings.cache_ttl_seconds)

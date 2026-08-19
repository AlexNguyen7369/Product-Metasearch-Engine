"""
Core search logic. Deliberately framework-agnostic — no FastAPI types in
this module — so this exact function can be reused as-is by an MCP tool
later (see the MCP migration note in stack.md) instead of being rewritten.
"""

from app.cache import redis_cache
from app.models.product import SearchResponse
from app.providers.serpapi_provider import fetch_google_shopping, normalize


async def search_products(query: str) -> SearchResponse:
    cache_key = redis_cache.build_cache_key(query)

    cached = await redis_cache.get_cached(cache_key)
    if cached is not None:
        return SearchResponse(query=query, cached=True, results=cached)

    raw_results = await fetch_google_shopping(query)
    products = normalize(raw_results)

    await redis_cache.set_cached(cache_key, [p.model_dump() for p in products])

    return SearchResponse(query=query, cached=False, results=products)

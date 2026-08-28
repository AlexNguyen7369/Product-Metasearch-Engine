"""
Core search logic. Deliberately framework-agnostic — no FastAPI types in
this module — so this exact function can be reused as-is by an MCP tool
later (see the MCP migration note in stack.md) instead of being rewritten.

Filtering/sorting/pagination are all applied here, after the cache lookup,
rather than baked into the cache key: each query text caches one superset
of results, and slicing/recomputing a different filter, sort, or page is
cheap to do in-process on every request instead of fragmenting the cache
per combination or making a second billable SerpAPI call per page.
"""

from typing import Optional

from app.cache import redis_cache
from app.models.product import Product, SearchResponse
from app.providers.serpapi_provider import fetch_google_shopping, normalize

# category is deliberately not a filter yet — SerpAPI's google_shopping
# results (and therefore Product) don't carry a category field, so there's
# nothing real to filter by. Add it here once a provider actually supplies it.
_SORT_KEYS = {
    "price-asc": lambda p: p.price,
    "price-desc": lambda p: -p.price,
    "rating-desc": lambda p: -(p.rating or 0),
}

_PAGE_SIZE = 10  # not client-configurable yet — one thing to vary at a time


async def search_products(
    query: str,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    sort: str = "relevance",
    page: int = 1,
) -> SearchResponse:
    cache_key = redis_cache.build_cache_key(query)

    cached = await redis_cache.get_cached(cache_key)
    if cached is not None:
        products = [Product(**item) for item in cached]
        was_cached = True
    else:
        raw_results = await fetch_google_shopping(query)
        products = normalize(raw_results)
        await redis_cache.set_cached(cache_key, [p.model_dump() for p in products])
        was_cached = False

    products = _filter(products, price_min, price_max)
    products = _sort(products, sort)
    total = len(products)
    page_products = _paginate(products, page)

    return SearchResponse(
        query=query,
        cached=was_cached,
        results=page_products,
        page=page,
        page_size=_PAGE_SIZE,
        total=total,
    )


def _filter(products: list[Product], price_min: Optional[float], price_max: Optional[float]) -> list[Product]:
    if price_min is not None:
        products = [p for p in products if p.price >= price_min]
    if price_max is not None:
        products = [p for p in products if p.price <= price_max]
    return products


def _sort(products: list[Product], sort: str) -> list[Product]:
    key = _SORT_KEYS.get(sort)
    if key is None:  # "relevance" (or anything unrecognized) — keep provider order
        return products
    return sorted(products, key=key)


def _paginate(products: list[Product], page: int) -> list[Product]:
    start = (page - 1) * _PAGE_SIZE
    return products[start : start + _PAGE_SIZE]

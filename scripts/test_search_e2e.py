#!/usr/bin/env python3
"""
Local end-to-end smoke test — not a unit test, not part of any test suite.

Verifies, against the real services, that:
  1. SERPAPI_API_KEY is set and actually works.
  2. search_products() (the exact function api/routes/search.py calls)
     returns usable, normalized products on a real cache miss.
  3. The result gets cached in Redis, and a repeat call is served from
     cache instead of hitting SerpAPI again.

This makes one real, billable SerpAPI call per run. Run manually; don't
wire this into CI.

Usage:
    python scripts/test_search_e2e.py ["search query"]

Run from the repo root so `.env` and the `app` package resolve correctly.

Requires:
  - SERPAPI_API_KEY set in .env (or the environment).
  - Redis reachable at REDIS_URL in .env. The checked-in .env.example
    points at the Docker Compose hostname (redis://redis:6379/0), which
    only resolves inside that network. To run this script from the host
    instead, either:
      - run it inside the container:
          docker-compose run --rm api python scripts/test_search_e2e.py
      - or point REDIS_URL at a locally reachable Redis, e.g.
          REDIS_URL=redis://localhost:6379/0 python scripts/test_search_e2e.py
        (with `docker-compose up redis` or a local `redis-server` running).
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cache import redis_cache  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.search_service import search_products  # noqa: E402

DEFAULT_QUERY = "wireless mouse"


def mask(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}…{key[-4:]}"


async def main(query: str) -> int:
    print("== Product Metasearch Engine — live end-to-end search test ==\n")

    if not settings.serpapi_api_key:
        print("FAIL: SERPAPI_API_KEY is not set (check .env).")
        return 1

    print(f"SerpAPI key: {mask(settings.serpapi_api_key)}")
    print(f"Redis URL:   {settings.redis_url}")
    print(f"Query:       {query!r}\n")

    cache_key = redis_cache.build_cache_key(query)
    try:
        client = redis_cache.get_redis_client()
        await client.delete(cache_key)
    except Exception as exc:
        print(f"FAIL: could not reach Redis at {settings.redis_url}: {exc!r}")
        return 1
    print("Cleared any existing cache entry for this query, to force a real miss.\n")

    # First call: expect a genuine cache miss and a real SerpAPI round trip.
    print("Calling search_products() (expect cache miss, real SerpAPI call)...")
    start = time.monotonic()
    try:
        first = await search_products(query)
    except Exception as exc:
        print(f"FAIL: search_products() raised: {exc!r}")
        return 1
    first_elapsed = time.monotonic() - start

    if first.cached:
        print("FAIL: first call reported cached=True — cache clear above didn't take.")
        return 1
    if not first.results:
        print("FAIL: SerpAPI call succeeded but normalized to zero products.")
        return 1

    sample = first.results[0]
    if sample.price <= 0 or not sample.title or not sample.source or not sample.link:
        print(f"FAIL: first result looks malformed: {sample!r}")
        return 1

    print(f"OK: {len(first.results)} result(s) in {first_elapsed:.2f}s (cached=False)")
    print(f"    sample: {sample.title!r} — {sample.currency} {sample.price} from {sample.source}\n")

    # Second call: same query should now be served straight from Redis.
    print("Calling search_products() again (expect cache hit)...")
    start = time.monotonic()
    second = await search_products(query)
    second_elapsed = time.monotonic() - start

    if not second.cached:
        print("FAIL: second call reported cached=False — Redis caching isn't working.")
        return 1
    if len(second.results) != len(first.results):
        print(
            f"FAIL: cached result count ({len(second.results)}) != live result count "
            f"({len(first.results)})."
        )
        return 1

    print(f"OK: {len(second.results)} result(s) in {second_elapsed:.2f}s (cached=True)")
    if second_elapsed >= first_elapsed:
        print(
            "WARN: cached call wasn't faster than the live call — caching may still be "
            "correct, but this is unexpected and worth a look."
        )

    print("\nAll checks passed: real SerpAPI key works, and search is cached end-to-end.")
    return 0


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    sys.exit(asyncio.run(main(query)))

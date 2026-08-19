"""
Adapter for SerpAPI's `google_shopping` engine — the only place in the
codebase that knows SerpAPI's request/response shape. If a second provider
or a retailer-specific API gets added later, it's a new file here;
services/ and everything above it stays unchanged.
"""

from typing import Any, Optional

import httpx

from app.core.config import settings
from app.models.product import Product

SERPAPI_URL = "https://serpapi.com/search.json"


async def fetch_google_shopping(query: str) -> list[dict[str, Any]]:
    """Call SerpAPI and return the raw shopping_results list."""
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": settings.serpapi_api_key,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(SERPAPI_URL, params=params)
        response.raise_for_status()
        data = response.json()
    return data.get("shopping_results", [])


def normalize(raw_results: list[dict[str, Any]]) -> list[Product]:
    """Map SerpAPI's raw shopping_results into the normalized Product schema."""
    products: list[Product] = []
    for item in raw_results:
        price = _parse_price(item.get("extracted_price") or item.get("price"))
        if price is None:
            continue  # price is the one required field — skip unusable listings

        products.append(
            Product(
                title=item.get("title", "Untitled"),
                price=price,
                currency="USD",
                source=item.get("source", "Unknown"),
                link=item.get("link") or item.get("product_link") or "",
                thumbnail=item.get("thumbnail"),
                stock=item.get("availability"),  # rarely populated by this engine
                rating=item.get("rating"),
                review_count=item.get("reviews"),
                shipping_cost=_parse_price(item.get("shipping")),
            )
        )
    return products


def _parse_price(value: Any) -> Optional[float]:
    """SerpAPI sometimes returns price as a number, sometimes as '$19.99'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None

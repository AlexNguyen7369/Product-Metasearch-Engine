"""
MCP tool wrappers around the search service.

Per app_structure.md: this module only ever imports from app.services,
never from app.api or app.providers directly. Each tool here is a thin
pass-through — no new logic, just adapting search_products()'s return
value into a plain dict for the MCP transport — mirroring how
api/routes/search.py wraps the same function for HTTP. See mcp.md for
why this exists and how it fits together.
"""

from typing import Literal, Optional

from app.services.search_service import search_products

SortOption = Literal["relevance", "price-asc", "price-desc", "rating-desc"]


async def search_products_tool(
    query: str,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    sort: SortOption = "relevance",
    page: int = 1,
) -> dict:
    """Search for products across the configured marketplace provider(s).

    Args:
        query: Free-text product search query, e.g. "wireless mouse".
        price_min: Optional minimum price filter.
        price_max: Optional maximum price filter.
        sort: relevance | price-asc | price-desc | rating-desc.
        page: 1-indexed page of results (10 per page).
    """
    result = await search_products(query, price_min=price_min, price_max=price_max, sort=sort, page=page)
    return result.model_dump()

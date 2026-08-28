"""
HTTP layer for search — thin glue only. Parse the request, call the
service, return its result. No business logic belongs in this file; if
you're tempted to add any here, it goes in services/search_service.py
instead.
"""

from typing import Literal, Optional

from fastapi import APIRouter, Query, Request

from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.product import SearchResponse
from app.services.search_service import search_products

router = APIRouter()

SortOption = Literal["relevance", "price-asc", "price-desc", "rating-desc"]


@router.get("/search", response_model=SearchResponse)
@limiter.limit(settings.rate_limit)
async def search(
    request: Request,
    q: str = Query(..., min_length=1, description="Product search query"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    sort: SortOption = Query("relevance", description="Sort order for results"),
    page: int = Query(1, ge=1, description="1-indexed page of results"),
):
    return await search_products(q, price_min=price_min, price_max=price_max, sort=sort, page=page)

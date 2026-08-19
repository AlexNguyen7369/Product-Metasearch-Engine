"""
HTTP layer for search — thin glue only. Parse the request, call the
service, return its result. No business logic belongs in this file; if
you're tempted to add any here, it goes in services/search_service.py
instead.
"""

from fastapi import APIRouter, Query, Request

from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.product import SearchResponse
from app.services.search_service import search_products

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
@limiter.limit(settings.rate_limit)
async def search(request: Request, q: str = Query(..., min_length=1, description="Product search query")):
    return await search_products(q)

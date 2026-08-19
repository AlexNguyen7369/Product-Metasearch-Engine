"""
Normalized product schema — the single source of truth for what a "product
result" looks like, imported by providers/, services/, and api/ alike.

Only price/currency are treated as guaranteed. Everything else is nullable
because coverage is inconsistent per listing/provider (see stack.md).
"""

from typing import Optional

from pydantic import BaseModel


class Product(BaseModel):
    title: str
    price: float
    currency: str = "USD"
    source: str  # retailer/seller name
    link: str
    thumbnail: Optional[str] = None
    stock: Optional[str] = None  # least reliable field across providers
    rating: Optional[float] = None
    review_count: Optional[int] = None
    shipping_cost: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    cached: bool
    results: list[Product]

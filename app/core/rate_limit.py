"""
Rate limiting setup, kept separate from main.py so routes (and the MCP
tools) can import a limiter without importing the whole app.

This protects against cost blowout: every unique search is a paid SerpAPI
call on a cache miss, so neither the HTTP endpoint nor the MCP tool that
wraps the same search_products() should be unbounded (see mcp.md).
"""

import time

from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# HTTP: per-client-IP, applied via @limiter.limit(settings.rate_limit) on
# the route — slowapi handles keying off the request itself.
limiter = Limiter(key_func=get_remote_address)

# MCP: stdio has no client IP to key on, but a stdio server process is
# already spawned per client/session, so one global bucket per process is
# the equivalent guard — reuses the same configured rate string as the
# HTTP limiter via the `limits` package slowapi is itself built on.
_mcp_rate_limit = parse(settings.rate_limit)
_mcp_limiter = FixedWindowRateLimiter(MemoryStorage())
_MCP_KEY = "mcp"


def check_mcp_rate_limit() -> tuple[bool, float]:
    """Record one MCP tool call attempt against the shared limit.

    Returns (allowed, retry_after_seconds). retry_after_seconds is only
    meaningful when allowed is False.
    """
    allowed = _mcp_limiter.hit(_mcp_rate_limit, _MCP_KEY)
    if allowed:
        return True, 0.0
    stats = _mcp_limiter.get_window_stats(_mcp_rate_limit, _MCP_KEY)
    return False, max(0.0, stats.reset_time - time.time())

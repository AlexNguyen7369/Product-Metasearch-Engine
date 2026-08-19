"""
Rate limiting setup (slowapi), kept separate from main.py so routes can
import `limiter` without importing the whole app.

This protects against cost blowout: every unique search is a paid SerpAPI
call on a cache miss, so the search endpoint should never be unbounded.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

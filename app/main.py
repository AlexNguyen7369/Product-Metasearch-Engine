"""
FastAPI app instance. Only wiring lives here: middleware, exception
handlers, routers, and the static frontend mount. No business logic.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes.search import router as search_router
from app.core.rate_limit import limiter

app = FastAPI(title="Product Metasearch Engine")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(search_router, prefix="/api")

# Mounted last, at "/", so it never shadows the /api routes above. Kept as
# plain static files — no build step — per stack.md.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

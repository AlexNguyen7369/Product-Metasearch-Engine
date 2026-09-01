# Current Progress

## Completed
1. 2026-08-18 — Alex Nguyen — Initialized repository with README.
2. 2026-08-19 — Alex Nguyen — Fixed repo structure: `.git` was rooted one
   level up in the parent `Personal-Projects` folder; moved it into
   `Product-Metasearch-Engine/` so this project is a standalone repo like the
   others.
3. 2026-08-19 — Alex Nguyen — Added `stack.md` documenting the chosen tech
   stack (FastAPI, Redis, SerpAPI) and the architectural change required for
   the future MCP server migration.
4. 2026-08-19 — Alex Nguyen — Added `current_progress.md` and a
   `CLAUDE.md` rule to keep it updated after every commit/push.
5. 2026-08-19 — Alex Nguyen — Added `app_structure.md`: planned folder
   layout (`api/` / `services/` / `providers/` / `cache/` / `models/` /
   `core/` / `mcp/`) with reasoning for each split.
6. 2026-08-19 — Alex Nguyen — Scaffolded the full app per `app_structure.md`:
   FastAPI app, `search_products()` service, SerpAPI provider + normalizer,
   Redis cache layer, rate limiting, `Product`/`SearchResponse` models,
   `mcp/tools.py` placeholder, plain HTML/JS frontend, Dockerfile +
   docker-compose. No real SerpAPI key wired up/tested yet — logic only.
7. 2026-08-22 — Alex Nguyen — Added a `/test` placeholder page
   (`frontend/test/index.html`, served via the existing
   `StaticFiles(html=True)` mount) and wired a "Test page" button in the
   frontend to navigate to it; the page itself does nothing yet.
8. 2026-08-27 — Alex Nguyen — Added a front-end scaffold for future
   marketplace features: an inert filters panel (category, price
   min/max, sort) and a disabled pagination bar on the search page,
   wired with IDs/handlers but not connected to `/api/search` yet.
9. 2026-08-28 — Alex Nguyen — Added `scripts/test_search_e2e.py` and ran
   it live: confirmed the real SerpAPI key works (40 normalized results
   for "wireless mouse") and that a repeat query is served from Redis
   (cached=True, 0.00s vs 4.43s live).
10. 2026-08-28 — Alex Nguyen — Wired `price_min`, `price_max`, and `sort`
    (relevance/price-asc/price-desc/rating-desc) query params to
    `/api/search`, applied in `search_service.py` after the cache lookup;
    verified live against the real API on both a fresh call and a cache
    hit. `category` stays unwired and its `<select>` is now disabled — no
    provider currently supplies category data to filter by.
11. 2026-08-28 — Alex Nguyen — Wired pagination to `/api/search`: `page`
    query param, `SearchResponse.page/page_size/total`, in-process slicing
    in `search_service.py`, and the frontend Prev/Next buttons + page
    indicator now use it. Verified live against the real API (contiguous
    pages, stable total, correct behavior past the last page).
12. 2026-09-01 — Alex Nguyen — Wired up the MCP tool wrapper:
    `app/mcp/tools.py` (`search_products_tool()`) and `app/mcp/server.py`
    (stdio `MCPServer`, run via `python -m app.mcp.server`), added
    `mcp>=2.0` to `requirements.txt`, and wrote `mcp.md` explaining the
    concepts. Verified live against the real API — `list_tools()` and
    `call_tool()` both work and return results matching `/api/search`.

## What's next
**Add MCP-side rate limiting** to `app/mcp/server.py`/`tools.py` — an
equivalent to `slowapi`'s per-IP limit on `/api/search`, since the
`slowapi` limiter is HTTP middleware and does not apply to MCP tool calls.

**Why this is next:** flagged explicitly as an open gap in `mcp.md` — an
MCP client can currently call `search_products_tool` at unlimited
frequency, and every cache miss still bills SerpAPI. `stack.md` states
protecting against that exact cost blowout was the reason `slowapi` was
added to the HTTP side in the first place; the MCP transport now has the
same exposure with no equivalent guard.

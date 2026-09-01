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
13. 2026-09-01 — Alex Nguyen — Added MCP-side rate limiting: a per-process
    `FixedWindowRateLimiter` (via `limits`, reusing `settings.rate_limit`)
    in `app/core/rate_limit.py`, checked in `search_products_tool` before
    calling `search_products()`, raising the SDK's `ToolError` so the
    message reaches the client. Verified against the real protocol
    handler (`_handle_call_tool`) with `RATE_LIMIT=2/minute`: calls 1-2
    succeeded, 3-4 correctly returned `is_error=True`.
14. 2026-09-01 — Alex Nguyen — Added `scripts/test_mcp_e2e.py`: spawns
    `python -m app.mcp.server` as a real subprocess and drives it with the
    `mcp` SDK's `ClientSession` over actual stdio (real `initialize`
    handshake, `list_tools()`, `call_tool()`) instead of calling
    `MCPServer`'s Python methods in-process. Verified live: real search
    results and the rate limiter's rejection both survive the real wire
    protocol unchanged.

## What's next
**Verify `docker-compose up` actually builds and runs the app end-to-end**
— the FastAPI + Redis stack has never been run through Docker; every
local verification so far (entries 9-14) used a manually-run Homebrew
Redis plus a scratch virtualenv as a substitute, because Docker wasn't
available in the environment doing the testing.

**Why this is next:** `docker-compose.yml`/`Dockerfile` are the documented,
intended local dev workflow (`stack.md`, `app_structure.md`) and have been
sitting untested since entry 6 (2026-08-19) — every other major piece
(search, filters/sort, pagination, MCP) has since been proven against the
real API, but always bypassing the one thing a new contributor would
actually run first.

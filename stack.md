# Tech Stack

## Backend
- **FastAPI** — async Python web framework. Async matters here because the core
  operation (search) fans out to external calls and shouldn't block on the
  slowest one.
- **Service-layer pattern** — business logic (query provider, normalize,
  cache) lives in plain Python functions separate from route handlers. Routes
  just call the function and return the result. See "MCP migration note"
  below for why this separation matters.
- **slowapi** — per-IP/per-key rate limiting on the search endpoint, to
  protect against cost blowout from a paid upstream API.

## Caching
- **Redis** — cache-first layer in front of the data provider. Every search
  checks Redis before calling out; only cache misses hit the paid API.
- TTL ~30-60 min per cached query (prices don't change second-to-second, and
  this directly controls API spend).
- Local via Docker for now.

## Data source
- **SerpAPI — `google_shopping` engine** — one paid call returns listings
  already aggregated from many retailers by Google Shopping. Chosen over
  integrating individual retailer APIs (auth/schema per retailer) and over
  scraping (fragile, ToS risk).
- Trade-off accepted: no control over which retailers appear in results,
  coverage depends on what Google Shopping surfaces.

## Data model
Normalized `Product` schema — only price/currency is treated as guaranteed;
everything else is nullable because coverage is inconsistent per listing:
- `price` + `currency` (required)
- `stock` / availability (nullable — least reliable field from this provider)
- `rating` + `review_count` (nullable, scales may vary)
- `shipping_cost` / delivery estimate (nullable)

## Storage
- **No central database for MVP.** Redis is ephemeral/query-keyed, not a
  system of record. Revisit if/when price history, watchlists, or user
  accounts are needed — none of that is cacheable in Redis alone.

## Frontend
- Plain HTML/JS, optionally HTMX or Alpine for interactivity. No build step.
  Calls the FastAPI REST API directly.

## Hosting
- Local via Docker Compose (FastAPI + Redis) for now, during experimentation.
- Deferred decision: cloud hosting (Render/Railway/Fly.io, or a
  serverless split with Upstash Redis) once ready to deploy beyond local.

---

## Architectural change required when converting to an MCP server

The **service layer must already be the boundary**, not the HTTP layer, for
this migration to be a wrap instead of a rewrite:

- Today: `FastAPI route -> service function (e.g. search_products(query)) -> Product[]`
- MCP: `MCP tool definition -> same service function -> Product[]`

An MCP tool is effectively "a function plus a schema." If `search_products`
and friends stay pure Python functions (no `Request`/`Response` objects, no
FastAPI-specific types in their signatures), they can be registered directly
as MCP tools later with a thin adapter, and the FastAPI app and the MCP
server can run side by side calling the same underlying logic.

What will need to change at that point:
- **Rate limiting** moves from HTTP middleware (slowapi) to whatever
  throttling the MCP transport/host supports — the HTTP-specific limiter
  won't apply to MCP tool calls.
- **Auth**, if added before the MCP migration, needs an equivalent on the
  MCP side (API keys/headers don't carry over the same way).
- **Redis cache** stays as-is — it sits below the service layer, so both the
  REST API and the MCP tools benefit from it unchanged.

The concrete rule going forward: never put logic directly in a FastAPI route
handler. If it's not trivial request/response glue, it belongs in a service
function.

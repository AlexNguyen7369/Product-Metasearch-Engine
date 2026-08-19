# App Structure

Planned folder layout, before any code is scaffolded. This is the blueprint
`current_progress.md`'s next task will follow.

```
Product-Metasearch-Engine/
├── app/                        # Backend (Python package)
│   ├── main.py                 # FastAPI app instance: mounts routes + middleware only
│   │
│   ├── api/                    # HTTP layer — thin glue, no logic
│   │   └── routes/
│   │       └── search.py       # /search route: parse request -> call service -> return
│   │
│   ├── services/                # Business logic, plain Python (no FastAPI types)
│   │   └── search_service.py   # search_products() — the function MCP will wrap later
│   │
│   ├── providers/               # Adapters to external data sources
│   │   └── serpapi_provider.py # SerpAPI request/response handling, isolated
│   │
│   ├── cache/
│   │   └── redis_cache.py      # get/set/TTL logic, generic — doesn't know about SerpAPI
│   │
│   ├── models/
│   │   └── product.py          # normalized Product schema (single source of truth)
│   │
│   ├── core/
│   │   ├── config.py           # env vars / settings
│   │   └── rate_limit.py       # slowapi setup
│   │
│   └── mcp/                    # (future, not built yet) MCP tool wrappers
│       └── tools.py            # will just import + expose services/, nothing else
│
├── frontend/                    # Plain HTML/JS/HTMX — separate from backend entirely
│   ├── index.html
│   └── static/
│       ├── js/
│       └── css/
│
├── docker-compose.yml           # FastAPI + Redis, local dev
├── Dockerfile
├── requirements.txt
├── stack.md
├── app_structure.md
├── current_progress.md
├── CLAUDE.md
└── README.md
```

## Why the breakdown is split this way

- **`api/` vs `services/` — the split that matters most.** Routes are
  disposable glue (parse a request, call a function, return it); the actual
  logic lives in `services/`. This is a direct consequence of the MCP
  migration note in `stack.md` — an MCP tool wraps a plain function, not a
  FastAPI route, so the reusable code has to already live outside the HTTP
  layer.

- **`providers/` isolated from `services/`.** Today there's one provider
  (SerpAPI). If a retailer API or a second data source gets added later,
  that's a new file in `providers/` — `services/` doesn't change. This keeps
  "how we talk to SerpAPI" from leaking into "what a search does," which
  matters for testing too: services can be tested against a fake provider
  without hitting the network.

- **`cache/` is generic, not SerpAPI-specific.** Caching logic (key
  generation, TTL) doesn't need to know what it's caching. Keeping it
  provider-agnostic means swapping Redis for something else later, or
  caching a second provider's results, doesn't touch this file.

- **`models/` as a single source of truth.** The normalized `Product` schema
  is imported by `api/`, `services/`, and `providers/` alike instead of each
  layer defining its own shape. One place to update when a field changes,
  instead of three places drifting out of sync.

- **`core/` for cross-cutting concerns.** Config and rate limiting don't
  belong to any one feature — keeping them out of `api/` or `services/`
  stops settings/middleware code from getting duplicated or scattered as
  more routes get added.

- **`mcp/` exists as a placeholder now, empty until it's actually built.**
  Having the folder reserved is a reminder that it should only ever import
  from `services/` — if it ever needs to reach into `api/` or `providers/`
  directly, that's a signal the service layer is leaking too little.

- **`frontend/` fully separate, not nested under `app/`.** Keeps the backend
  independently testable/deployable — the frontend could be swapped for
  something else, or later split into its own repo/deploy, without touching
  backend code at all.

- **Net effect on scalability/clutter:** each folder has exactly one reason
  to change (a new retailer = `providers/`, a new endpoint = `api/`, a new
  cache backend = `cache/`). That keeps unrelated changes from touching the
  same files, which is what actually keeps a codebase from turning into a
  tangle as more retailers/providers/routes get added.

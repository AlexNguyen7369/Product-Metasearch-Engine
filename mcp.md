# MCP Server

What `app/mcp/` is, why it exists, and the technical concepts behind it.
Companion to `stack.md`'s "Architectural change required when converting
to an MCP server" section — this is that migration, done.

## What MCP is, briefly

The Model Context Protocol (MCP) is a standard way to expose
tools/data to an LLM client (Claude Desktop, Claude Code, etc.) as a
small, typed API the model can call directly — instead of the model
needing a human to run `curl` against a REST endpoint, or a
model-specific integration being written per client. A client connects
to an MCP server, asks it "what tools do you have?", gets back a name +
description + JSON schema per tool, and can then call one by name with
arguments matching that schema. It's a transport and a discovery
convention, not a different way of writing business logic.

That last point is why this file exists as a companion to `stack.md`
rather than a replacement for it: nothing about *what a search does*
changed. Only a second way to reach it got added.

## Why this repo has two transports now

- **`/api/search`** (`app/api/routes/search.py`) — HTTP, for the browser
  frontend in `frontend/`.
- **`search_products_tool`** (`app/mcp/tools.py`, run via
  `app/mcp/server.py`) — MCP, for an LLM client to call directly.

Both call the exact same function: `search_products()` in
`app/services/search_service.py`. Neither transport contains any search
logic of its own — they're both thin adapters translating their
transport's request shape into a call to that one function, and its
return value back into their transport's response shape. This was the
whole point of keeping `search_products()` framework-agnostic from the
start (see `stack.md`): adding MCP support meant writing ~25 lines
across two new files and touching zero existing ones.

```
FastAPI route  ─┐
                ├─► search_products(query, price_min, price_max, sort, page) ─► Product[]
MCP tool       ─┘
```

## The two new files

- **`app/mcp/tools.py`** — `search_products_tool()`, an `async def` with
  the same parameters as `/api/search`'s query params (`query`,
  `price_min`, `price_max`, `sort`, `page`). It calls `search_products()`
  and returns `result.model_dump()` — a plain dict, because MCP tool
  results cross a process/transport boundary and can't carry a Pydantic
  model. Per `app_structure.md`'s rule for this folder, it imports only
  from `app.services` — never `app.api` or `app.providers`.

- **`app/mcp/server.py`** — the actual MCP server process. Creates an
  `MCPServer` instance, registers `search_products_tool` on it, and runs
  it over **stdio**. Run with:

  ```
  python -m app.mcp.server
  ```

  This is a separate, standalone process from `uvicorn app.main:app` —
  they don't share a Python process, only the Redis instance and
  SerpAPI key they're both configured to use.

## Technical concepts worth understanding

**stdio transport.** The MCP server doesn't open a network port. It
reads JSON-RPC requests from stdin and writes responses to stdout —
that's the whole transport. This is the standard way a local MCP server
talks to a local client (the client spawns the server as a subprocess
and owns its stdin/stdout pipes); it's why the server exits cleanly the
moment stdin closes, with no client to serve. `MCPServer.run()` also
supports `sse` and `streamable-http` transports for a server that
should be reachable over a network instead of spawned as a subprocess —
not used here, since this server always runs alongside the app that
spawns it.

**Schema generation from type hints.** The tool's JSON schema (what a
client sees when it asks "what arguments does this tool take?") is
generated automatically from `search_products_tool`'s signature and
docstring — not hand-written. `sort: Literal["relevance", "price-asc",
"price-desc", "rating-desc"]` becomes a JSON Schema `enum`;
`Optional[float] = None` becomes a nullable number with that default.
This is the same reason FastAPI can generate OpenAPI docs from a route
signature — same idea, different schema format, both driven by Python
type hints doing double duty as the API contract.

**The `mcp` SDK's v2 rename.** The Python `mcp` package went through a
breaking rename: what most existing tutorials call `FastMCP` (imported
from `mcp.server.fastmcp`) is `MCPServer` (imported from
`mcp.server.mcpserver`) as of `mcp` 2.x, which is what `requirements.txt`
pins (`mcp>=2.0`). The decorator-based API (`@mcp.tool()`) is unchanged;
only the class name and import path moved. Worth knowing if a search
turns up `FastMCP` example code that doesn't import in this repo — it's
not wrong, it's the pre-2.0 name.

**A tool function stays a plain function.** `mcp.tool()(search_products_tool)`
registers the function *and returns it unchanged* — the decorator's
effect is entirely in the server's internal tool registry, not in
wrapping/transforming the function itself. That's why `tools.py` has no
MCP-specific imports at all: `search_products_tool` is importable and
directly callable (e.g. from a test, or a script) with no MCP server
running, the same way `search_products()` always has been.

## What did *not* change

Per the `stack.md` migration note, this is the part of that note that's
now been executed:

- **Redis caching** — unchanged, sits below the service layer, so both
  transports get cache hits/misses identically.
- **`search_service.py` / `serpapi_provider.py` / `models/product.py`** —
  zero edits. The MCP layer only calls in, it never changes what it's
  calling.

And the part still open, as predicted:

- **Rate limiting** — `slowapi`'s limiter is HTTP middleware
  (`app/core/rate_limit.py`); it does not apply to MCP tool calls. An MCP
  client can currently call `search_products_tool` at unlimited
  frequency, each miss still billing SerpAPI. Needs an equivalent
  throttle before this is exposed to an untrusted MCP client — fine for
  now since it only runs locally, spawned by a trusted client.
- **Auth** — none exists on either transport yet, so nothing new is owed
  here specifically because of MCP; noted in case auth gets added to the
  HTTP side first, since it would need a separate mechanism here (MCP
  doesn't share HTTP headers/cookies).
- **`category`** — still unwired on both transports. Not an MCP gap: no
  provider supplies category data at all (see `search_service.py`).

## Verified

Ran `app/mcp/server.py`'s `search_products_tool` directly against the
real SerpAPI key and a local Redis: `list_tools()` returned the correct
JSON schema (enum for `sort`, nullable numbers for `price_min`/
`price_max`), and `call_tool("search_products_tool", {"query": "wireless
mouse", "sort": "price-asc", "price_min": 10, "price_max": 30})` returned
real, correctly filtered/sorted/paginated results — the same shape
`/api/search` returns, confirming both transports really do share one
code path rather than two parallel implementations that happen to agree
today.

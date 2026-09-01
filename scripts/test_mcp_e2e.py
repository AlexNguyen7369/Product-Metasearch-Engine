#!/usr/bin/env python3
"""
Local end-to-end smoke test for the MCP server — not a unit test, not
part of any test suite.

Unlike every other MCP check so far (see mcp.md), this does NOT call
MCPServer's Python methods (call_tool(), _handle_call_tool()) directly
in-process. It spawns `python -m app.mcp.server` as a real subprocess and
talks to it as a genuine MCP client would: over stdio, through the SDK's
ClientSession, doing a real JSON-RPC initialize handshake before ever
listing or calling a tool. That's the one layer of app/mcp/ every prior
check skipped.

Two phases:
  1. Spawn the server normally, list tools, call search_products_tool
     with a real query — makes one real, billable SerpAPI call (or a
     Redis-cached one) through the actual stdio transport.
  2. Spawn a second server instance with RATE_LIMIT=2/minute, call the
     tool 3 times back to back, and confirm the 3rd comes back as a
     protocol-level is_error result with the expected message — i.e.
     that rate limiting (see app/core/rate_limit.py) actually survives
     the trip through stdio, not just a direct Python call.

Usage:
    python scripts/test_mcp_e2e.py ["search query"]

Run from the repo root so `.env` and the `app` package resolve correctly
in both this process and the spawned server subprocess (same interpreter,
via sys.executable).

Requires the same things scripts/test_search_e2e.py does: SERPAPI_API_KEY
set, and Redis reachable at REDIS_URL (see that script's docstring for
notes on running outside Docker).
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import types  # noqa: E402
from mcp.client.session import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_QUERY = "wireless mouse"


def server_params(extra_env: dict[str, str] | None = None) -> StdioServerParameters:
    env = dict(os.environ)
    env.update(extra_env or {})
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
        cwd=REPO_ROOT,
        env=env,
    )


async def call_tool(session: ClientSession, query: str, **kwargs) -> types.CallToolResult:
    result = await session.call_tool("search_products_tool", {"query": query, **kwargs})
    if not isinstance(result, types.CallToolResult):
        raise TypeError(f"expected CallToolResult, got {type(result).__name__}")
    return result


async def check_real_call(query: str) -> bool:
    print("== Phase 1: real stdio round trip (spawned subprocess) ==\n")
    async with stdio_client(server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Initialized session with spawned `python -m app.mcp.server`.")

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            if "search_products_tool" not in names:
                print(f"FAIL: search_products_tool not in list_tools() result: {names}")
                return False
            print(f"OK: list_tools() returned {names}\n")

            print(f"Calling search_products_tool(query={query!r}) over stdio...")
            result = await call_tool(session, query)
            if result.is_error:
                print(f"FAIL: call_tool returned is_error=True: {result.content}")
                return False

            text = result.content[0].text
            data = json.loads(text)
            if not data.get("results"):
                print(f"FAIL: zero results in tool response: {data}")
                return False

            sample = data["results"][0]
            print(f"OK: {data['total']} total result(s), page {data['page']} of size {data['page_size']}")
            print(f"    sample: {sample['title']!r} — {sample['currency']} {sample['price']} from {sample['source']}\n")
            return True


async def check_rate_limit_over_stdio() -> bool:
    print("== Phase 2: rate limiting survives the stdio round trip ==\n")
    async with stdio_client(server_params({"RATE_LIMIT": "2/minute"})) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            outcomes = []
            for i in range(3):
                result = await call_tool(session, DEFAULT_QUERY)
                outcomes.append(result.is_error)
                label = "is_error=True" if result.is_error else "is_error=False"
                print(f"  call {i + 1}: {label}")

            if outcomes != [False, False, True]:
                print(f"FAIL: expected [False, False, True], got {outcomes}")
                return False

            message = result.content[0].text  # the 3rd (rejected) call's message
            if "Rate limit exceeded" not in message:
                print(f"FAIL: rejected call's message doesn't mention the rate limit: {message!r}")
                return False

            print(f"OK: 3rd call rejected over stdio with: {message!r}\n")
            return True


async def main(query: str) -> int:
    print("== Product Metasearch Engine — MCP server real-connection test ==\n")

    if not await check_real_call(query):
        return 1
    if not await check_rate_limit_over_stdio():
        return 1

    print("All checks passed: the MCP server works end-to-end over a real stdio connection.")
    return 0


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    sys.exit(asyncio.run(main(q)))

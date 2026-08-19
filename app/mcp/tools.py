"""
Placeholder for the future MCP server integration — intentionally not
built yet (see current_progress.md).

Per app_structure.md: this module should only ever import from
app.services, never from app.api or app.providers directly. Each MCP tool
will be a thin wrapper around a service function, mirroring how
api/routes/search.py wraps search_products() today — the same pattern,
just a different transport.
"""

# from app.services.search_service import search_products
#
# async def search_products_tool(query: str) -> dict:
#     # MCP tool wrapper around the same logic the /api/search route calls.
#     result = await search_products(query)
#     return result.model_dump()

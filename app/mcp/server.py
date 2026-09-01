"""
MCP server entrypoint. Exposes the tools in tools.py to MCP clients
(e.g. Claude Desktop, Claude Code) over stdio — a separate transport
from the HTTP API in app/main.py, running as its own process alongside
it rather than replacing it. See mcp.md for the concepts behind this.

Run with:
    python -m app.mcp.server
"""

from mcp.server.mcpserver import MCPServer

from app.mcp.tools import search_products_tool

mcp = MCPServer("product-metasearch-engine")
mcp.tool()(search_products_tool)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

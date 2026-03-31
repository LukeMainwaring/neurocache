"""Entry point for running the MCP server via stdio: python -m neurocache.mcp"""

from neurocache.mcp.server import mcp

mcp.run(transport="stdio")

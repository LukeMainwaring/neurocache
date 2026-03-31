"""Entry point for running the MCP server via stdio: python -m neurocache.mcp"""

import logging
import sys

# Configure logging to stderr before importing the server (stdout is
# reserved for the MCP stdio JSON-RPC protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

from neurocache.mcp.server import mcp  # noqa: E402

mcp.run(transport="stdio")

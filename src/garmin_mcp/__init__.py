"""Garmin Running MCP Server."""

from mcp.server.fastmcp import FastMCP

from garmin_mcp.auth import create_client
from garmin_mcp.client import GarminClient

mcp = FastMCP("garmin-mcp")

_client: GarminClient | None = None


def get_client() -> GarminClient:
    """Get the authenticated Garmin client (lazy initialization)."""
    global _client
    if _client is None:
        garmin = create_client()
        _client = GarminClient(garmin)
    return _client


# Register all tools
from garmin_mcp.tools import register_tools  # noqa: E402

register_tools(mcp)


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")

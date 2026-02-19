"""Register all MCP tools."""

from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP):
    """Register all tool modules with the MCP server."""
    from garmin_mcp.tools import (
        activities,
        summary,
        training,
        heart_rate,
        wellness,
        records,
        workout,
        gear,
    )

    activities.register(mcp)
    summary.register(mcp)
    training.register(mcp)
    heart_rate.register(mcp)
    wellness.register(mcp)
    records.register(mcp)
    workout.register(mcp)
    gear.register(mcp)

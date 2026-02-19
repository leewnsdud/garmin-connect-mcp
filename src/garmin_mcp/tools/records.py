"""Personal records and goals tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP):
    @mcp.tool()
    def get_personal_records() -> list[dict[str, Any]]:
        """Get all personal records (PRs) including best times for
        various distances (1K, 1 mile, 5K, 10K, half marathon, marathon).
        Essential for Jack Daniels VDOT calculation.
        """
        from garmin_mcp import get_client

        client = get_client()
        return client.get_personal_record()

    @mcp.tool()
    def get_goals(status: str = "active") -> list[dict[str, Any]]:
        """Get fitness goals and their progress.

        Args:
            status: Goal status filter - "active", "completed", or "all" (default: "active")
        """
        from garmin_mcp import get_client

        client = get_client()
        return client.get_goals(status=status)

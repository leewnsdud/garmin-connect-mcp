"""Heart rate and HRV tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import today_str


def register(mcp: FastMCP):
    @mcp.tool()
    def get_heart_rate_data(date: str = "") -> dict[str, Any]:
        """Get daily heart rate data including resting HR, max HR, and average HR.
        Useful for tracking fitness trends and recovery.

        Args:
            date: Date (YYYY-MM-DD), defaults to today
        """
        from garmin_mcp import get_client

        client = get_client()
        d = date or today_str()

        hr_data = client.get_heart_rates(d)

        try:
            rhr_data = client.get_rhr_day(d)
        except Exception:
            rhr_data = None

        return {
            "heart_rates": hr_data,
            "resting_heart_rate": rhr_data,
        }

    @mcp.tool()
    def get_hrv_data(date: str = "") -> dict[str, Any]:
        """Get Heart Rate Variability (HRV) data. Higher HRV indicates
        better recovery status. Important for training load management.

        Args:
            date: Date (YYYY-MM-DD), defaults to today
        """
        from garmin_mcp import get_client

        client = get_client()
        d = date or today_str()
        return client.get_hrv_data(d)

    @mcp.tool()
    def get_activity_hr_zones(activity_id: int) -> dict[str, Any]:
        """Get heart rate zone distribution for a specific activity.
        Shows time spent in each HR zone. Essential for 80/20 training
        analysis and intensity distribution monitoring.

        Args:
            activity_id: The Garmin activity ID
        """
        from garmin_mcp import get_client

        client = get_client()
        zones = client.get_activity_hr_in_timezones(activity_id)

        # Calculate percentages if we have zone data
        if isinstance(zones, list) and zones:
            total_seconds = sum(z.get("secsInZone", 0) for z in zones)
            if total_seconds > 0:
                for zone in zones:
                    secs = zone.get("secsInZone", 0)
                    zone["percentage"] = round((secs / total_seconds) * 100, 1)

        return {
            "activity_id": activity_id,
            "hr_zones": zones,
        }

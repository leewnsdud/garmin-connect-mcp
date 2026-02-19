"""Running gear (shoes) management tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP):
    @mcp.tool()
    def get_running_gear() -> list[dict[str, Any]]:
        """Get running gear (shoes) list with cumulative distance and activity count.
        Useful for tracking shoe mileage and knowing when to replace shoes
        (typically every 500-800 km).
        """
        from garmin_mcp import get_client

        client = get_client()

        profile_id = client.get_profile_id()
        gear_list = client.get_gear(profile_id)

        running_gear = []
        for gear in gear_list:
            gear_type = gear.get("gearTypeName", "").lower()
            if "shoe" in gear_type or "running" in gear_type or not gear_type:
                gear_info: dict[str, Any] = {
                    "uuid": gear.get("uuid"),
                    "name": gear.get("displayName") or gear.get("gearMakeName", ""),
                    "model": gear.get("gearModelName", ""),
                    "status": gear.get("gearStatusName", ""),
                    "date_begin": gear.get("dateBegin"),
                    "date_end": gear.get("dateEnd"),
                }

                try:
                    stats = client.get_gear_stats(gear.get("uuid", ""))
                    gear_info["total_distance_km"] = round(
                        stats.get("totalDistance", 0) / 1000, 2
                    ) if stats.get("totalDistance") else 0
                    gear_info["total_activities"] = stats.get("totalActivities", 0)
                except Exception:
                    gear_info["total_distance_km"] = None
                    gear_info["total_activities"] = None

                running_gear.append(gear_info)

        return running_gear

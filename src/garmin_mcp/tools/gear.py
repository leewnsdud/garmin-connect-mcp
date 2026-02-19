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

                # Max distance limit set by user (meters)
                max_meters = gear.get("maximumMeters")
                if max_meters and max_meters > 0:
                    gear_info["max_distance_km"] = round(max_meters / 1000, 1)
                else:
                    gear_info["max_distance_km"] = None

                try:
                    stats = client.get_gear_stats(gear.get("uuid", ""))
                    total_dist = stats.get("totalDistance", 0)
                    gear_info["total_distance_km"] = round(
                        total_dist / 1000, 2
                    ) if total_dist else 0
                    gear_info["total_activities"] = stats.get("totalActivities", 0)

                    # Wear percentage based on user-set max distance
                    if max_meters and max_meters > 0 and total_dist:
                        gear_info["wear_percentage"] = round(
                            (total_dist / max_meters) * 100, 1
                        )
                    else:
                        gear_info["wear_percentage"] = None
                except Exception:
                    gear_info["total_distance_km"] = None
                    gear_info["total_activities"] = None
                    gear_info["wear_percentage"] = None

                running_gear.append(gear_info)

        return running_gear

"""Running activity tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import today_str
from garmin_mcp.sanitize import strip_pii


RUNNING_TYPE_KEYS = {"running", "track_running", "trail_running", "treadmill_running"}


def _is_running(activity: dict[str, Any]) -> bool:
    """Check if an activity is a running activity."""
    # List API uses "activityType", detail API uses "activityTypeDTO"
    activity_type = activity.get("activityType") or activity.get("activityTypeDTO") or {}
    type_key = activity_type.get("typeKey", "")
    parent_type_key = activity_type.get("parentTypeKey", "")
    return type_key in RUNNING_TYPE_KEYS or parent_type_key == "running"


def _format_pace(seconds_per_km: float | None) -> str | None:
    """Format pace from seconds/km to mm:ss string."""
    if seconds_per_km is None or seconds_per_km <= 0:
        return None
    minutes = int(seconds_per_km // 60)
    secs = int(seconds_per_km % 60)
    return f"{minutes}:{secs:02d}"


def _build_split_summary(split_summaries: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    """Build a concise run/walk/stand summary from splitSummaries (RWD data).

    This is particularly useful for trail running where Garmin auto-detects
    running, walking, and standing segments.
    """
    if not split_summaries:
        return None
    rwd_types = {"RWD_RUN", "RWD_WALK", "RWD_STAND"}
    result = {}
    for s in split_summaries:
        stype = s.get("splitType", "")
        if stype not in rwd_types:
            continue
        label = stype.replace("RWD_", "").lower()
        avg_speed = s.get("averageSpeed")
        avg_pace = _format_pace((1000 / avg_speed) if avg_speed and avg_speed > 0 else None)
        # List API uses totalAscent (centimeters), detail API uses elevationGain (meters)
        total_ascent = s.get("totalAscent")
        elevation_gain_val = s.get("elevationGain")
        if total_ascent is not None:
            elev_gain = round(total_ascent / 100, 1)
        elif elevation_gain_val is not None:
            elev_gain = round(elevation_gain_val, 1)
        else:
            elev_gain = 0.0

        result[label] = {
            "distance_km": round(s.get("distance", 0) / 1000, 2),
            "duration_seconds": round(s.get("duration", 0), 1),
            "avg_pace": avg_pace,
            "elevation_gain": elev_gain,
            "elevation_loss": s.get("elevationLoss"),
        }
    return result or None


def _summarize_activity(activity: dict[str, Any]) -> dict[str, Any]:
    """Extract key running fields from an activity."""
    distance_m = activity.get("distance", 0)
    duration_s = activity.get("duration", 0)
    avg_pace_s = (duration_s / (distance_m / 1000)) if distance_m > 0 else None
    max_speed = activity.get("maxSpeed")
    max_pace_s = (1000 / max_speed) if max_speed and max_speed > 0 else None

    return {
        "activity_id": activity.get("activityId"),
        "name": activity.get("activityName"),
        "date": activity.get("startTimeLocal"),
        "type": activity.get("activityType", {}).get("typeKey"),
        "distance_km": round(distance_m / 1000, 2) if distance_m else 0,
        "duration_seconds": round(duration_s, 1) if duration_s else 0,
        "moving_duration_seconds": round(activity["movingDuration"], 1) if activity.get("movingDuration") else None,
        "avg_pace": _format_pace(avg_pace_s),
        "max_pace": _format_pace(max_pace_s),
        "avg_heart_rate": activity.get("averageHR"),
        "max_heart_rate": activity.get("maxHR"),
        "avg_cadence": activity.get("averageRunningCadenceInStepsPerMinute"),
        "max_cadence": activity.get("maxRunningCadenceInStepsPerMinute"),
        "avg_stride_length_cm": round(activity["avgStrideLength"], 1) if activity.get("avgStrideLength") else None,
        "avg_ground_contact_time_ms": round(activity["avgGroundContactTime"], 1) if activity.get("avgGroundContactTime") else None,
        "avg_vertical_oscillation_cm": round(activity["avgVerticalOscillation"], 1) if activity.get("avgVerticalOscillation") else None,
        "avg_vertical_ratio": round(activity["avgVerticalRatio"], 1) if activity.get("avgVerticalRatio") else None,
        "calories": activity.get("calories"),
        "elevation_gain": activity.get("elevationGain"),
        "elevation_loss": activity.get("elevationLoss"),
        "max_elevation": activity.get("maxElevation"),
        "min_elevation": activity.get("minElevation"),
        "avg_power": activity.get("avgPower"),
        "max_power": activity.get("maxPower"),
        "normalized_power": activity.get("normPower"),
        "training_effect_aerobic": activity.get("aerobicTrainingEffect"),
        "training_effect_anaerobic": activity.get("anaerobicTrainingEffect"),
        "training_load": activity.get("activityTrainingLoad"),
        "training_effect_label": activity.get("trainingEffectLabel"),
        "vo2max": activity.get("vO2MaxValue"),
        "fastest_split_1km": _format_pace(activity.get("fastestSplit_1000")),
        "fastest_split_1mile": _format_pace(activity.get("fastestSplit_1609")),
        "fastest_split_5km": _format_pace(activity.get("fastestSplit_5000")),
        "hr_zone_1_seconds": activity.get("hrTimeInZone_1"),
        "hr_zone_2_seconds": activity.get("hrTimeInZone_2"),
        "hr_zone_3_seconds": activity.get("hrTimeInZone_3"),
        "hr_zone_4_seconds": activity.get("hrTimeInZone_4"),
        "hr_zone_5_seconds": activity.get("hrTimeInZone_5"),
        "steps": activity.get("steps"),
        "lap_count": activity.get("lapCount"),
        "is_pr": activity.get("pr"),
        "max_temperature": activity.get("maxTemperature"),
        "min_temperature": activity.get("minTemperature"),
        # Trail running fields
        "avg_grade_adjusted_pace": _format_pace(
            (1000 / activity["avgGradeAdjustedSpeed"]) if activity.get("avgGradeAdjustedSpeed") else None
        ),
        "max_vertical_speed": activity.get("maxVerticalSpeed"),
        "water_estimated_ml": activity.get("waterEstimated"),
        "split_summary": _build_split_summary(activity.get("splitSummaries")),
    }


def register(mcp: FastMCP):
    @mcp.tool()
    def get_recent_activities(count: int = 20) -> list[dict[str, Any]]:
        """Get recent running activities. Returns a list of running activities
        with key metrics like distance, pace, heart rate, cadence, and elevation.

        Args:
            count: Number of activities to return (default: 20, max: 100)
        """
        from garmin_mcp import get_client

        client = get_client()
        count = min(count, 100)

        # Fetch more than needed to account for non-running activities
        activities = client.get_activities(start=0, limit=count * 3)

        running = []
        for activity in activities:
            if _is_running(activity):
                running.append(_summarize_activity(activity))
                if len(running) >= count:
                    break

        return running

    @mcp.tool()
    def get_activities_by_date(
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """Get running activities within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        from garmin_mcp import get_client

        client = get_client()
        activities = client.get_activities_by_date(start_date, end_date, "running")

        return [_summarize_activity(a) for a in activities if _is_running(a)]

    @mcp.tool()
    def get_activity_detail(activity_id: int) -> dict[str, Any]:
        """Get full details of a specific running activity including
        pace, heart rate, cadence, elevation, training effect, and more.

        Args:
            activity_id: The Garmin activity ID
        """
        from garmin_mcp import get_client

        client = get_client()
        activity = client.get_activity(activity_id)

        # Detail API nests data in summaryDTO and activityTypeDTO
        summary = activity.get("summaryDTO", {})
        activity_type = activity.get("activityTypeDTO", {})

        distance_m = summary.get("distance", 0)
        duration_s = summary.get("duration", 0)
        avg_pace_s = (duration_s / (distance_m / 1000)) if distance_m > 0 else None

        return {
            "activity_id": activity.get("activityId"),
            "name": activity.get("activityName"),
            "date": summary.get("startTimeLocal"),
            "type": activity_type.get("typeKey"),
            "distance_km": round(distance_m / 1000, 2) if distance_m else 0,
            "duration_seconds": round(duration_s, 1) if duration_s else 0,
            "avg_pace": _format_pace(avg_pace_s),
            "avg_heart_rate": summary.get("averageHR"),
            "max_heart_rate": summary.get("maxHR"),
            "min_heart_rate": summary.get("minHR"),
            "avg_cadence": summary.get("averageRunCadence"),
            "max_cadence": summary.get("maxRunCadence"),
            "calories": summary.get("calories"),
            "elevation_gain": summary.get("elevationGain"),
            "elevation_loss": summary.get("elevationLoss"),
            "min_elevation": summary.get("minElevation"),
            "max_elevation": summary.get("maxElevation"),
            "avg_power": summary.get("averagePower"),
            "max_power": summary.get("maxPower"),
            "normalized_power": summary.get("normalizedPower"),
            "training_effect_aerobic": summary.get("trainingEffect"),
            "training_effect_anaerobic": summary.get("anaerobicTrainingEffect"),
            "training_load": summary.get("activityTrainingLoad"),
            "training_label": summary.get("trainingEffectLabel"),
            "avg_stride_length": summary.get("strideLength"),
            "avg_vertical_oscillation": summary.get("verticalOscillation"),
            "avg_ground_contact_time": summary.get("groundContactTime"),
            "avg_vertical_ratio": summary.get("verticalRatio"),
            "avg_temperature": summary.get("averageTemperature"),
            "max_temperature": summary.get("maxTemperature"),
            "min_temperature": summary.get("minTemperature"),
            "steps": summary.get("steps"),
            "description": activity.get("description"),
            # Trail running fields
            "avg_grade_adjusted_pace": _format_pace(
                (1000 / summary["avgGradeAdjustedSpeed"]) if summary.get("avgGradeAdjustedSpeed") else None
            ),
            "max_vertical_speed": summary.get("maxVerticalSpeed"),
            "water_estimated_ml": summary.get("waterEstimated"),
            "impact_load": summary.get("impactLoad"),
            "begin_potential_stamina": summary.get("beginPotentialStamina"),
            "end_potential_stamina": summary.get("endPotentialStamina"),
            "min_available_stamina": summary.get("minAvailableStamina"),
            "split_summary": _build_split_summary(activity.get("splitSummaries")),
        }

    @mcp.tool()
    def get_activity_splits(activity_id: int) -> dict[str, Any]:
        """Get split data (per km/mile) for a running activity.
        Useful for analyzing pacing strategy (positive/negative splits).

        Args:
            activity_id: The Garmin activity ID
        """
        from garmin_mcp import get_client

        client = get_client()
        splits = client.get_activity_splits(activity_id)
        splits = strip_pii(splits)

        # Convert speed fields to pace in each lap
        for lap in splits.get("lapDTOs", []):
            for speed_key, pace_key in [
                ("averageSpeed", "avg_pace"),
                ("averageMovingSpeed", "avg_moving_pace"),
                ("maxSpeed", "max_pace"),
                ("avgGradeAdjustedSpeed", "grade_adjusted_pace"),
            ]:
                speed = lap.pop(speed_key, None)
                lap[pace_key] = _format_pace(
                    (1000 / speed) if speed and speed > 0 else None
                )
            # maxVerticalSpeed is vertical climbing rate (m/s), not running speed
            # Keep as-is since it's not a pace metric

        return splits

    @mcp.tool()
    def get_activity_weather(activity_id: int) -> dict[str, Any]:
        """Get weather conditions during a running activity.
        Returns temperature, humidity, wind, and weather description.
        Useful for trail running analysis where weather impacts performance.

        Args:
            activity_id: The Garmin activity ID
        """
        from garmin_mcp import get_client

        client = get_client()
        weather = client.get_activity_weather(activity_id)
        weather = strip_pii(weather)
        # Remove location fields from weather (station coordinates approximate user location)
        weather.pop("latitude", None)
        weather.pop("longitude", None)
        return weather

    @mcp.tool()
    def get_activity_typed_splits(activity_id: int) -> dict[str, Any]:
        """Get ClimbPro and terrain-typed splits for a running activity.
        Returns climb segments with grade, difficulty rating, elevation data,
        and grade-adjusted pace. Essential for trail running analysis.

        Each split includes:
        - type: CLIMB_PRO_CYCLING_CLIMB or CLIMB_PRO_CYCLING_CLIMB_SECTION
        - climbProDifficulty: DESCENT, LOW, MODERATE, STEEP, STEEPER, STEEPEST,
          or cycling-style categories (FOURTH_CATEGORY to HC)
        - averageGrade, maxGrade: slope percentage
        - avgGradeAdjustedSpeed: grade-adjusted speed (m/s)
        - elevationGain, elevationLoss, startElevation

        Args:
            activity_id: The Garmin activity ID
        """
        from garmin_mcp import get_client

        client = get_client()
        data = client.get_activity_typed_splits(activity_id)

        # Summarize the splits to reduce response size
        splits = data.get("splits", [])
        climb_splits = []
        for s in splits:
            stype = s.get("type", "")
            # Only include climb segments, skip RWD/INTERVAL
            if "CLIMB" not in stype:
                continue
            gap_speed = s.get("avgGradeAdjustedSpeed")
            gap_pace = _format_pace((1000 / gap_speed) if gap_speed and gap_speed > 0 else None)
            avg_speed = s.get("averageSpeed")
            actual_pace = _format_pace((1000 / avg_speed) if avg_speed and avg_speed > 0 else None)

            climb_splits.append({
                "type": stype,
                "difficulty": s.get("climbProDifficulty"),
                "distance_km": round(s.get("distance", 0) / 1000, 2),
                "duration_seconds": round(s.get("duration", 0), 1),
                "elevation_gain": s.get("elevationGain"),
                "elevation_loss": s.get("elevationLoss"),
                "start_elevation": s.get("startElevation"),
                "avg_grade": s.get("averageGrade"),
                "max_grade": s.get("maxGrade"),
                "actual_pace": actual_pace,
                "grade_adjusted_pace": gap_pace,
                "avg_heart_rate": s.get("averageHR"),
                "max_heart_rate": s.get("maxHR"),
                "avg_power": s.get("averagePower"),
                "avg_cadence": s.get("averageRunCadence"),
            })

        return {
            "activity_id": data.get("activityId"),
            "total_climb_splits": len(climb_splits),
            "splits": climb_splits,
        }

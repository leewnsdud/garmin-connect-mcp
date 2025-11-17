#!/usr/bin/env python3
"""Analytics-focused handler functions for Garmin Connect MCP."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, tzinfo
from typing import Any, Dict, List, Optional

from services.garmin_client import GarminClientService
from utils import (
    filter_running_activities,
    format_pace,
    normalize_distance_to_km,
)


async def get_weekly_running_summary(
    service: GarminClientService,
    args: Dict[str, Any],
    timezone: Optional[tzinfo] = None,
) -> Dict[str, Any]:
    garmin = service.client
    weeks_back = args.get("weeks_back", 1)

    summaries = []
    now = datetime.now(timezone)
    for week in range(max(1, int(weeks_back))):
        end_date = now - timedelta(weeks=week)
        start_date = end_date - timedelta(days=7)

        activities = await asyncio.to_thread(
            garmin.get_activities_by_date,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )

        running_activities = filter_running_activities(activities)

        total_distance = sum(a.get("distance", 0) for a in running_activities) / 1000
        total_duration = sum(a.get("duration", 0) for a in running_activities) / 3600
        run_count = len(running_activities)

        avg_pace = None
        if total_distance > 0 and total_duration > 0:
            avg_pace_seconds = (total_duration * 3600) / total_distance
            avg_pace = format_pace(avg_pace_seconds)

        longest_run = max(
            (a.get("distance", 0) / 1000 for a in running_activities),
            default=0,
        )
        total_elevation = sum(
            a.get("elevationGain", 0) for a in running_activities
        )

        week_summary = {
            "week_start": start_date.strftime("%Y-%m-%d"),
            "week_end": end_date.strftime("%Y-%m-%d"),
            "total_runs": run_count,
            "total_distance_km": round(total_distance, 2),
            "total_duration_hours": round(total_duration, 2),
            "average_pace_per_km": avg_pace,
            "longest_run_km": round(longest_run, 2),
            "total_elevation_gain_m": round(total_elevation, 1),
            "average_run_distance_km": round(total_distance / run_count, 2) if run_count > 0 else 0,
            "activities": [
                {
                    "date": a.get("startTimeLocal"),
                    "distance_km": round(a.get("distance", 0) / 1000, 2),
                    "duration_minutes": round(a.get("duration", 0) / 60, 1),
                    "pace_per_km": format_pace(
                        (a.get("duration", 0) / a.get("distance", 1)) * 1000
                    ) if a.get("distance", 0) > 0 else None,
                }
                for a in running_activities[:10]
            ],
        }

        summaries.append(week_summary)

    trends = None
    if len(summaries) >= 2:
        current_week = summaries[0]
        previous_week = summaries[1]
        distance_delta = current_week["total_distance_km"] - previous_week["total_distance_km"]
        trends = {
            "distance_change_km": round(distance_delta, 2),
            "distance_change_percent": round(
                (distance_delta / max(previous_week["total_distance_km"], 1)) * 100,
                1,
            ),
            "run_count_change": current_week["total_runs"] - previous_week["total_runs"],
        }

    return {
        "weekly_summaries": summaries,
        "trends": trends,
        "analysis_period": f"{weeks_back} week(s)",
    }


async def get_gear_insights(
    service: GarminClientService,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    garmin = service.client

    threshold = args.get("distance_threshold_km", 800)
    include_retired = args.get("include_retired", False)
    max_items = args.get("max_items", 5)

    try:
        threshold_km = max(100, int(threshold))
    except (TypeError, ValueError):
        threshold_km = 800

    try:
        max_items_int = max(1, min(int(max_items), 10))
    except (TypeError, ValueError):
        max_items_int = 5

    device_info = await asyncio.to_thread(garmin.get_device_last_used)
    if not device_info or not isinstance(device_info, dict):
        return {"error": "Unable to determine user profile for gear lookup."}

    user_profile_number = device_info.get("userProfileNumber")
    if not user_profile_number:
        return {"error": "Device metadata did not include userProfileNumber."}

    gear_payload = await asyncio.to_thread(garmin.get_gear, user_profile_number)

    if isinstance(gear_payload, dict):
        if isinstance(gear_payload.get("userGear"), list):
            gear_items = gear_payload.get("userGear")
        elif isinstance(gear_payload.get("gear"), list):
            gear_items = gear_payload.get("gear")
        else:
            gear_items = list(gear_payload.values())
    elif isinstance(gear_payload, list):
        gear_items = gear_payload
    else:
        gear_items = []

    running_gear = []
    for gear in gear_items:
        if not isinstance(gear, dict):
            continue
        activity_type = str(
            gear.get("activityType")
            or gear.get("activityTypeKey")
            or gear.get("sportTypeKey")
            or ""
        ).lower()
        if "run" not in activity_type:
            continue
        if not include_retired:
            status = str(gear.get("gearStatus") or "").lower()
            if status in {"retired", "inactive"}:
                continue
        running_gear.append(gear)

    def gear_distance_key(item: Dict[str, Any]) -> float:
        candidates = [
            item.get("totalDistance"),
            item.get("totalDistanceInMeters"),
            item.get("lifetimeDistance"),
        ]
        for cand in candidates:
            dist = normalize_distance_to_km(cand)
            if dist is not None:
                return dist
        return 0.0

    running_gear.sort(key=gear_distance_key, reverse=True)
    running_gear = running_gear[:max_items_int]

    gear_summaries: List[Dict[str, Any]] = []
    alerts: List[str] = []

    for gear in running_gear:
        gear_uuid = gear.get("gearUuid") or gear.get("gearUuidId")
        gear_name = gear.get("displayName") or gear.get("customDisplayName")
        gear_status = gear.get("gearStatus")
        brand = gear.get("brand")
        model = gear.get("model")

        stats = {}
        if gear_uuid:
            stats = await asyncio.to_thread(garmin.get_gear_stats, gear_uuid) or {}

        distance_candidates = [
            stats.get("totalDistance"),
            stats.get("totalDistanceInMeters"),
            stats.get("lifetimeDistance"),
            gear.get("totalDistance"),
            gear.get("totalDistanceInMeters"),
        ]

        distance_km = None
        for candidate in distance_candidates:
            distance_km = normalize_distance_to_km(candidate)
            if distance_km is not None:
                break

        activity_count = (
            stats.get("totalActivities")
            or stats.get("activityCount")
            or gear.get("activityCount")
        )
        last_used = stats.get("lastUsed") or gear.get("lastActivityDate")

        status = "unknown"
        recommendation = "Distance data unavailable; monitor usage manually."
        wear_percentage = None

        if distance_km is not None:
            wear_percentage = round((distance_km / threshold_km) * 100, 1)
            if distance_km >= threshold_km:
                status = "replace"
                recommendation = (
                    "Mileage exceeds threshold – consider replacing or rotating."
                )
                alerts.append(
                    f"{gear_name or gear_uuid} has {distance_km:.0f} km (>{threshold_km} km)."
                )
            elif distance_km >= threshold_km * 0.9:
                status = "warning"
                recommendation = (
                    "Approaching mileage limit – plan a replacement soon."
                )
                alerts.append(
                    f"{gear_name or gear_uuid} nearing limit with {distance_km:.0f} km."
                )
            else:
                status = "ok"
                recommendation = "Mileage within acceptable range."

        gear_summary = {
            "name": gear_name,
            "brand": brand,
            "model": model,
            "status": gear_status,
            "distance_km": distance_km,
            "usage_percent": wear_percentage,
            "activities": activity_count,
            "last_used": last_used,
            "lifecycle_status": status,
            "recommendation": recommendation,
            "gear_uuid": gear_uuid,
        }
        gear_summaries.append({k: v for k, v in gear_summary.items() if v is not None})

    total_activities = await asyncio.to_thread(garmin.count_activities)

    return {
        "total_activities": total_activities,
        "threshold_km": threshold_km,
        "gear_items_analyzed": len(gear_summaries),
        "gear_summary": gear_summaries,
        "alerts": alerts,
        "metadata": {
            "include_retired": include_retired,
            "max_items": max_items_int,
            "user_profile_number": user_profile_number,
        },
        "note": "Consider rotating shoes before the mileage threshold to reduce injury risk.",
    }
#!/usr/bin/env python3
"""Training-related handler functions for Garmin Connect MCP."""

from __future__ import annotations

from typing import Any, Dict

from services.garmin_client import GarminClientService
from utils import (
    build_training_plan_schedule_preview,
    summarize_training_plan_detail,
    summarize_training_plans,
)


async def list_training_plans(
    service: GarminClientService,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    goal_distance = args.get("goal_distance")
    experience_level = args.get("experience_level")
    max_items = args.get("max_items", 5)

    try:
        max_items_int = max(1, min(int(max_items), 20))
    except (TypeError, ValueError):
        max_items_int = 5

    plans_response = await service.load_training_plans()
    summary = summarize_training_plans(
        plans_response,
        goal_distance=goal_distance,
        experience_level=experience_level,
        max_items=max_items_int,
    )

    total_response_count = len(plans_response.get("trainingPlanList") or [])
    summary["metadata"] = {
        "total_plans_in_response": total_response_count,
        "plan_ids": [plan.get("id") for plan in summary.get("plans", []) if plan.get("id")],
    }

    return summary


async def get_training_plan_overview(
    service: GarminClientService,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    plan_id_raw = args.get("plan_id")
    schedule_weeks = args.get("schedule_weeks", 4)

    try:
        plan_id = int(plan_id_raw)
    except (TypeError, ValueError):
        raise ValueError("plan_id must be an integer value")

    try:
        schedule_weeks_int = max(1, min(int(schedule_weeks), 16))
    except (TypeError, ValueError):
        schedule_weeks_int = 4

    plans_response = await service.load_training_plans()
    detail_bundle = await service.fetch_training_plan_detail(
        plan_id,
        plans_response=plans_response,
    )
    plan_detail = detail_bundle.get("detail") or {}

    overview = summarize_training_plan_detail(
        plan_detail,
        schedule_weeks=schedule_weeks_int,
    )

    overview["metadata"] = {
        "plan_id": plan_id,
        "plan_name": detail_bundle.get("metadata", {}).get("plan_name"),
        "plan_category": detail_bundle.get("metadata", {}).get("plan_category"),
        "schedule_weeks_preview": schedule_weeks_int,
    }

    return overview


async def get_training_plan_schedule(
    service: GarminClientService,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    plan_id_raw = args.get("plan_id")
    weeks = args.get("weeks", 6)
    include_calendar = args.get("include_calendar", True)

    try:
        plan_id = int(plan_id_raw)
    except (TypeError, ValueError):
        raise ValueError("plan_id must be an integer value")

    try:
        weeks_int = max(1, min(int(weeks), 20))
    except (TypeError, ValueError):
        weeks_int = 6

    plans_response = await service.load_training_plans()
    detail_bundle = await service.fetch_training_plan_detail(
        plan_id,
        plans_response=plans_response,
    )
    plan_detail = detail_bundle.get("detail") or {}

    schedule = build_training_plan_schedule_preview(plan_detail, weeks=weeks_int)

    response: Dict[str, Any] = {
        "plan_id": plan_id,
        "plan_name": detail_bundle.get("metadata", {}).get("plan_name"),
        "plan_category": detail_bundle.get("metadata", {}).get("plan_category"),
        "schedule": schedule,
        "metadata": {
            "weeks_requested": weeks_int,
        },
    }

    if include_calendar:
        calendar_list = plans_response.get("trainingPlanCalendarList") or []
        selected_calendar = None
        for entry in calendar_list:
            if not isinstance(entry, dict):
                continue
            try:
                current_id = int(entry.get("trainingPlanId") or entry.get("id"))
            except (TypeError, ValueError):
                continue
            if current_id == plan_id:
                selected_calendar = entry
                break

        if selected_calendar:
            calendar_entries = (
                selected_calendar.get("calendarEntries")
                or selected_calendar.get("entries")
                or []
            )
            upcoming = []
            if isinstance(calendar_entries, list):
                for entry in calendar_entries:
                    if not isinstance(entry, dict):
                        continue
                    workout_info = entry.get("workout")
                    if isinstance(workout_info, dict):
                        workout_name = workout_info.get("workoutName")
                        workout_id = workout_info.get("trainingPlanWorkoutId")
                    else:
                        workout_name = entry.get("workoutName")
                        workout_id = entry.get("trainingPlanWorkoutId")

                    summary = {
                        "date": entry.get("calendarDate") or entry.get("date"),
                        "phase": entry.get("phaseName") or entry.get("phase"),
                        "workout_name": workout_name,
                        "workout_id": workout_id,
                    }
                    summary = {k: v for k, v in summary.items() if v is not None}
                    if summary:
                        upcoming.append(summary)
                    if len(upcoming) >= min(weeks_int * 3, 12):
                        break

            response["calendar_alignment"] = {
                "start_date": selected_calendar.get("startDate") or selected_calendar.get("startDay"),
                "end_date": selected_calendar.get("endDate"),
                "upcoming_workouts": upcoming,
                "note": "Limited to upcoming scheduled workouts."
                if upcoming
                else "Calendar entries available but no upcoming workouts found.",
            }
        else:
            response["calendar_alignment"] = {
                "note": "No personal calendar entries found for this training plan."
            }

    return response
"""Workout creation and management tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.sanitize import strip_pii


def _parse_pace_to_speed(pace_str: str) -> float:
    """Convert pace string (e.g. '4:30' min/km) to speed in m/s."""
    parts = pace_str.split(":")
    minutes = int(parts[0])
    seconds = int(parts[1]) if len(parts) > 1 else 0
    total_seconds_per_km = minutes * 60 + seconds
    if total_seconds_per_km <= 0:
        raise ValueError(f"Invalid pace: {pace_str}")
    return 1000 / total_seconds_per_km  # m/s


def _build_target(target: dict[str, Any] | None) -> tuple[dict[str, Any] | None, float | None, float | None]:
    """Build target info for workout steps.

    Returns (target_type_dict, target_value_one, target_value_two).
    """
    if not target:
        return None, None, None

    target_type = target.get("type", "no_target")

    # IMPORTANT: garminconnect library TargetType constants are WRONG.
    # Actual Garmin API target type mapping (verified by upload + re-fetch):
    #   1 = no.target
    #   2 = power.zone      (library says HEART_RATE - WRONG)
    #   3 = cadence          (library says CADENCE - correct)
    #   4 = heart.rate.zone  (library says SPEED - WRONG)
    #   5 = speed.zone       (library says POWER - WRONG)
    #   6 = pace.zone        (library says OPEN - WRONG)
    if target_type == "pace":
        min_pace = target.get("min", "")
        max_pace = target.get("max", "")
        if min_pace and max_pace:
            # Garmin expects targetValueOne <= targetValueTwo (low speed to high speed)
            speed_a = _parse_pace_to_speed(min_pace)
            speed_b = _parse_pace_to_speed(max_pace)
            return (
                {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone"},
                min(speed_a, speed_b),
                max(speed_a, speed_b),
            )
    elif target_type == "heart_rate":
        min_hr = target.get("min", 0)
        max_hr = target.get("max", 0)
        if min_hr and max_hr:
            return (
                {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                float(min_hr),
                float(max_hr),
            )
    elif target_type == "cadence":
        min_cad = target.get("min", 0)
        max_cad = target.get("max", 0)
        if min_cad and max_cad:
            return (
                {"workoutTargetTypeId": 3, "workoutTargetTypeKey": "cadence.zone"},
                float(min_cad),
                float(max_cad),
            )
    elif target_type == "power":
        min_power = target.get("min", 0)
        max_power = target.get("max", 0)
        if min_power and max_power:
            return (
                {"workoutTargetTypeId": 2, "workoutTargetTypeKey": "power.zone"},
                float(min_power),
                float(max_power),
            )

    return None, None, None


def _build_end_condition(step_def: dict[str, Any]) -> tuple[dict[str, Any], float]:
    """Build end condition from step definition.

    Supports duration_seconds (time-based) and distance_meters (distance-based).
    Returns (end_condition_dict, end_condition_value).
    """
    # IMPORTANT: garminconnect library ConditionType constants are WRONG for some IDs.
    # Actual Garmin API condition type mapping (verified by upload + re-fetch):
    #   1 = lap.button       (library says DISTANCE - WRONG)
    #   2 = time             (library says TIME - correct)
    #   3 = distance         (library says HEART_RATE - WRONG)
    #   4 = calories         (library says CALORIES - correct)
    #   5 = power            (library says CADENCE - WRONG)
    #   6 = heart.rate       (library says POWER - WRONG)
    #   7 = iterations       (library says ITERATIONS - correct)
    #   8 = fixed.rest

    distance = step_def.get("distance_meters")
    if distance is not None and distance > 0:
        return (
            {
                "conditionTypeId": 3,
                "conditionTypeKey": "distance",
                "displayOrder": 3,
                "displayable": True,
            },
            float(distance),
        )

    duration = step_def.get("duration_seconds")
    if duration is not None and duration > 0:
        return (
            {
                "conditionTypeId": 2,
                "conditionTypeKey": "time",
                "displayOrder": 2,
                "displayable": True,
            },
            float(duration),
        )

    # No duration or distance specified → lap button (press lap to advance)
    return (
        {
            "conditionTypeId": 1,
            "conditionTypeKey": "lap.button",
            "displayOrder": 1,
            "displayable": True,
        },
        0.0,
    )


_STEP_TYPE_MAP = {
    "warmup": (1, "warmup"),
    "cooldown": (2, "cooldown"),
    "interval": (3, "interval"),
    "recovery": (4, "recovery"),
    "rest": (5, "rest"),
}


def _build_steps(steps: list[dict[str, Any]], start_order: int = 1) -> tuple[list[Any], int]:
    """Build workout steps from simplified step definitions.

    Returns (list of step objects, next step order).
    """
    from garminconnect.workout import (
        ExecutableStep,
        create_repeat_group,
    )

    result = []
    order = start_order

    for step_def in steps:
        step_type = step_def.get("type", "interval")

        if step_type in _STEP_TYPE_MAP:
            type_id, type_key = _STEP_TYPE_MAP[step_type]
            end_condition, end_value = _build_end_condition(step_def)
            target_type, val_one, val_two = _build_target(step_def.get("target"))

            if target_type is None:
                target_type = {
                    "workoutTargetTypeId": 1,
                    "workoutTargetTypeKey": "no.target",
                    "displayOrder": 1,
                }

            s = ExecutableStep(
                type="ExecutableStepDTO",
                stepOrder=order,
                stepType={"stepTypeId": type_id, "stepTypeKey": type_key, "displayOrder": type_id},
                endCondition=end_condition,
                endConditionValue=end_value,
                targetType=target_type,
            )
            if val_one is not None:
                s.targetValueOne = val_one
            if val_two is not None:
                s.targetValueTwo = val_two
            if step_def.get("description"):
                s.description = step_def["description"]
            result.append(s)
            order += 1

        elif step_type == "repeat":
            count = step_def.get("count", 1)
            inner_steps_def = step_def.get("steps", [])
            inner_steps, _ = _build_steps(inner_steps_def, start_order=1)
            group = create_repeat_group(
                iterations=count,
                workout_steps=inner_steps,
                step_order=order,
            )
            if step_def.get("skip_last_rest", False):
                group.skipLastRestStep = True
            result.append(group)
            order += 1

    return result, order


def _estimate_duration(steps_def: list[dict[str, Any]]) -> int:
    """Estimate total workout duration in seconds.

    For distance-based steps, uses a rough estimate of 5:00/km pace.
    """
    total = 0
    for s in steps_def:
        if s.get("type") == "repeat":
            count = s.get("count", 1)
            inner = _estimate_duration(s.get("steps", []))
            total += count * inner
        elif s.get("distance_meters"):
            # Estimate: ~5:00/km = 300 sec/km
            total += int(s["distance_meters"] / 1000 * 300)
        else:
            total += s.get("duration_seconds", 0)
    return total


def register(mcp: FastMCP):
    @mcp.tool()
    def create_running_workout(
        name: str,
        steps: list[dict[str, Any]],
        description: str = "",
    ) -> dict[str, Any]:
        """Create a structured running workout and upload it to Garmin Connect.
        The workout will be synced to your Garmin watch.

        Each step has a 'type' (warmup, interval, recovery, rest, cooldown, repeat)
        and either 'duration_seconds' (time-based), 'distance_meters' (distance-based),
        or neither (lap button - press lap to advance to next step).
        Repeat steps have 'count' and nested 'steps'.
        Optionally set a 'target' with type (pace, heart_rate, cadence, power) and min/max values.
        Each step can have a 'description' for notes.
        Repeat steps can have 'skip_last_rest': true to skip the last recovery step.

        Example steps for a 4x1km distance-based interval workout:
        [
            {"type": "warmup", "duration_seconds": 600, "description": "Easy jog"},
            {"type": "repeat", "count": 4, "skip_last_rest": true, "steps": [
                {"type": "interval", "distance_meters": 1000, "target": {"type": "pace", "min": "4:30", "max": "4:50"}},
                {"type": "recovery", "duration_seconds": 120}
            ]},
            {"type": "cooldown", "duration_seconds": 600}
        ]

        Args:
            name: Workout name (e.g. "4x1km Intervals")
            steps: List of workout step definitions
            description: Optional workout description/notes
        """
        from garminconnect.workout import RunningWorkout, WorkoutSegment
        from garmin_mcp import get_client

        client = get_client()

        workout_steps, _ = _build_steps(steps)
        estimated_duration = _estimate_duration(steps)

        segment = WorkoutSegment(
            segmentOrder=1,
            sportType={"sportTypeId": 1, "sportTypeKey": "running"},
            workoutSteps=workout_steps,
        )

        workout = RunningWorkout(
            workoutName=name,
            estimatedDurationInSecs=estimated_duration,
            workoutSegments=[segment],
        )
        if description:
            workout.description = description

        result = client.upload_running_workout(workout)
        return strip_pii({
            "status": "created",
            "workout_name": name,
            "estimated_duration_seconds": estimated_duration,
            "result": result,
        })

    @mcp.tool()
    def get_workouts(count: int = 20) -> list[dict[str, Any]]:
        """Get list of saved workouts from Garmin Connect.

        Args:
            count: Number of workouts to return (default: 20, max: 100)
        """
        from garmin_mcp import get_client

        client = get_client()
        count = min(count, 100)
        return strip_pii(client.get_workouts(start=0, limit=count))

"""Workout creation and management tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP


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

    if target_type == "pace":
        min_pace = target.get("min", "")
        max_pace = target.get("max", "")
        if min_pace and max_pace:
            # Garmin uses speed (m/s) with pace.zone target type
            # min pace (slower) = lower speed, max pace (faster) = higher speed
            return (
                {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone", "displayOrder": 6},
                _parse_pace_to_speed(min_pace),
                _parse_pace_to_speed(max_pace),
            )
    elif target_type == "heart_rate":
        min_hr = target.get("min", 0)
        max_hr = target.get("max", 0)
        if min_hr and max_hr:
            return (
                {"workoutTargetTypeId": 2, "workoutTargetTypeKey": "heart.rate.zone"},
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

    return None, None, None


def _build_steps(steps: list[dict[str, Any]], start_order: int = 1) -> tuple[list[Any], int]:
    """Build workout steps from simplified step definitions.

    Returns (list of step objects, next step order).
    """
    from garminconnect.workout import (
        create_warmup_step,
        create_interval_step,
        create_recovery_step,
        create_cooldown_step,
        create_repeat_group,
    )

    result = []
    order = start_order

    step_creators = {
        "warmup": create_warmup_step,
        "cooldown": create_cooldown_step,
        "interval": create_interval_step,
        "recovery": create_recovery_step,
    }

    for step_def in steps:
        step_type = step_def.get("type", "interval")
        duration = step_def.get("duration_seconds", 300)
        target_type, val_one, val_two = _build_target(step_def.get("target"))

        if step_type in step_creators:
            s = step_creators[step_type](
                duration_seconds=duration,
                step_order=order,
                target_type=target_type,
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


def register(mcp: FastMCP):
    @mcp.tool()
    def create_running_workout(
        name: str,
        steps: list[dict[str, Any]],
        description: str = "",
    ) -> dict[str, Any]:
        """Create a structured running workout and upload it to Garmin Connect.
        The workout will be synced to your Garmin watch.

        Each step has a 'type' (warmup, interval, recovery, cooldown, repeat)
        and 'duration_seconds'. Repeat steps have 'count' and nested 'steps'.
        Optionally set a 'target' with type (pace, heart_rate, cadence) and min/max values.
        Each step can have a 'description' for notes.
        Repeat steps can have 'skip_last_rest': true to skip the last recovery step.

        Example steps for a 4x1km interval workout:
        [
            {"type": "warmup", "duration_seconds": 600, "description": "Easy jog"},
            {"type": "repeat", "count": 4, "skip_last_rest": true, "steps": [
                {"type": "interval", "duration_seconds": 300, "target": {"type": "pace", "min": "4:30", "max": "4:50"}},
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

        # Calculate estimated total duration
        def _estimate_duration(steps_def: list[dict[str, Any]]) -> int:
            total = 0
            for s in steps_def:
                if s.get("type") == "repeat":
                    count = s.get("count", 1)
                    inner = _estimate_duration(s.get("steps", []))
                    total += count * inner
                else:
                    total += s.get("duration_seconds", 0)
            return total

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
        return {
            "status": "created",
            "workout_name": name,
            "estimated_duration_seconds": estimated_duration,
            "result": result,
        }

    @mcp.tool()
    def get_workouts(count: int = 20) -> list[dict[str, Any]]:
        """Get list of saved workouts from Garmin Connect.

        Args:
            count: Number of workouts to return (default: 20, max: 100)
        """
        from garmin_mcp import get_client

        client = get_client()
        count = min(count, 100)
        return client.get_workouts(start=0, limit=count)

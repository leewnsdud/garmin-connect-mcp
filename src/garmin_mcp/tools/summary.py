"""Weekly and monthly running summary tools."""

import calendar
from datetime import date, datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import today_str
from garmin_mcp.tools.activities import _is_running


def _compute_summary(activities: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute summary statistics for a list of activities."""
    if not activities:
        return {
            "total_runs": 0,
            "total_distance_km": 0,
            "total_duration_seconds": 0,
            "avg_pace": None,
            "avg_heart_rate": None,
            "total_elevation_gain": 0,
            "longest_run_km": 0,
            "longest_run_pace": None,
        }

    total_distance_m = sum(a.get("distance", 0) or 0 for a in activities)
    total_duration_s = sum(a.get("duration", 0) or 0 for a in activities)
    total_elevation = sum(a.get("elevationGain", 0) or 0 for a in activities)

    hrs = [a.get("averageHR") for a in activities if a.get("averageHR")]
    avg_hr = round(sum(hrs) / len(hrs), 1) if hrs else None

    avg_pace_s = (total_duration_s / (total_distance_m / 1000)) if total_distance_m > 0 else None

    # Find longest run
    longest = max(activities, key=lambda a: a.get("distance", 0) or 0)
    longest_dist = (longest.get("distance", 0) or 0) / 1000
    longest_dur = longest.get("duration", 0) or 0
    longest_pace_s = (longest_dur / longest_dist) if longest_dist > 0 else None

    def fmt_pace(s: float | None) -> str | None:
        if s is None or s <= 0:
            return None
        return f"{int(s // 60)}:{int(s % 60):02d}"

    return {
        "total_runs": len(activities),
        "total_distance_km": round(total_distance_m / 1000, 2),
        "total_duration_seconds": round(total_duration_s, 1),
        "avg_pace": fmt_pace(avg_pace_s),
        "avg_heart_rate": avg_hr,
        "total_elevation_gain": round(total_elevation, 1),
        "longest_run_km": round(longest_dist, 2),
        "longest_run_pace": fmt_pace(longest_pace_s),
    }


def register(mcp: FastMCP):
    @mcp.tool()
    def get_weekly_running_summary(
        end_date: str = "",
        weeks: int = 1,
    ) -> list[dict[str, Any]]:
        """Get weekly running summary with total distance, runs, avg pace,
        elevation, heart rate, and longest run info.

        Args:
            end_date: End date (YYYY-MM-DD), defaults to today
            weeks: Number of weeks to include (default: 1, max: 12)
        """
        from garmin_mcp import get_client

        client = get_client()
        end = date.fromisoformat(end_date) if end_date else date.today()
        weeks = min(weeks, 12)

        results = []
        for w in range(weeks):
            week_end = end - timedelta(weeks=w)
            # Find Monday of that week
            week_start = week_end - timedelta(days=week_end.weekday())
            week_end_date = week_start + timedelta(days=6)

            activities = client.get_activities_by_date(
                week_start.isoformat(),
                week_end_date.isoformat(),
                "running",
            )

            running = [a for a in activities if _is_running(a)]
            summary = _compute_summary(running)
            summary["week_start"] = week_start.isoformat()
            summary["week_end"] = week_end_date.isoformat()
            results.append(summary)

        return results

    @mcp.tool()
    def get_monthly_running_summary(
        year: int = 0,
        month: int = 0,
    ) -> dict[str, Any]:
        """Get monthly running summary with total distance, runs, avg pace,
        weekly breakdown, and comparison with previous month.

        Args:
            year: Year (e.g. 2025), defaults to current year
            month: Month (1-12), defaults to current month
        """
        from garmin_mcp import get_client

        client = get_client()
        today = date.today()
        if year == 0:
            year = today.year
        if month == 0:
            month = today.month

        # Current month
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        activities = client.get_activities_by_date(
            start_date.isoformat(),
            end_date.isoformat(),
            "running",
        )
        running = [a for a in activities if _is_running(a)]
        current_summary = _compute_summary(running)

        # Weekly breakdown within the month
        weekly_breakdown = []
        week_start = start_date
        week_num = 1
        while week_start <= end_date:
            week_end = min(week_start + timedelta(days=6), end_date)
            week_activities = [
                a for a in running
                if week_start.isoformat() <= (a.get("startTimeLocal", "")[:10] or "") <= week_end.isoformat()
            ]
            week_summary = _compute_summary(week_activities)
            week_summary["week_number"] = week_num
            week_summary["week_start"] = week_start.isoformat()
            week_summary["week_end"] = week_end.isoformat()
            weekly_breakdown.append(week_summary)
            week_start = week_end + timedelta(days=1)
            week_num += 1

        # Previous month for comparison
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        prev_start = date(prev_year, prev_month, 1)
        prev_last_day = calendar.monthrange(prev_year, prev_month)[1]
        prev_end = date(prev_year, prev_month, prev_last_day)

        prev_activities = client.get_activities_by_date(
            prev_start.isoformat(),
            prev_end.isoformat(),
            "running",
        )
        prev_running = [a for a in prev_activities if _is_running(a)]
        prev_summary = _compute_summary(prev_running)

        # Compute change
        def pct_change(current: float, previous: float) -> float | None:
            if previous == 0:
                return None
            return round(((current - previous) / previous) * 100, 1)

        return {
            "year": year,
            "month": month,
            **current_summary,
            "weekly_breakdown": weekly_breakdown,
            "vs_previous_month": {
                "distance_change_pct": pct_change(
                    current_summary["total_distance_km"],
                    prev_summary["total_distance_km"],
                ),
                "runs_change": current_summary["total_runs"] - prev_summary["total_runs"],
                "previous_month_distance_km": prev_summary["total_distance_km"],
                "previous_month_runs": prev_summary["total_runs"],
            },
        }

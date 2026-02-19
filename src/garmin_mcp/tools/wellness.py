"""Wellness and recovery tools (sleep, stress, body battery, etc.)."""

from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import today_str


def register(mcp: FastMCP):
    @mcp.tool()
    def get_sleep_data(date: str = "") -> dict[str, Any]:
        """Get sleep data including duration, sleep stages (deep, light, REM),
        and sleep score. Sleep quality impacts training readiness.

        Args:
            date: Date (YYYY-MM-DD), defaults to today
        """
        from garmin_mcp import get_client

        client = get_client()
        d = date or today_str()
        return client.get_sleep_data(d)

    @mcp.tool()
    def get_daily_wellness(date: str = "") -> dict[str, Any]:
        """Get comprehensive daily wellness data: stress level, Body Battery,
        SpO2 (blood oxygen), and respiration rate. Helps assess recovery
        and readiness for training.

        Args:
            date: Date (YYYY-MM-DD), defaults to today
        """
        from garmin_mcp import get_client

        client = get_client()
        d = date or today_str()

        result: dict[str, Any] = {"date": d}

        try:
            result["stress"] = client.get_stress_data(d)
        except Exception:
            result["stress"] = None

        try:
            result["body_battery"] = client.get_body_battery(d)
        except Exception:
            result["body_battery"] = None

        try:
            result["spo2"] = client.get_spo2_data(d)
        except Exception:
            result["spo2"] = None

        try:
            result["respiration"] = client.get_respiration_data(d)
        except Exception:
            result["respiration"] = None

        return result

    @mcp.tool()
    def get_weekly_wellness_summary(
        end_date: str = "",
        weeks: int = 1,
    ) -> list[dict[str, Any]]:
        """Get weekly wellness trends: daily stress, Body Battery, sleep scores.
        Useful for correlating recovery patterns with training load.

        Args:
            end_date: End date (YYYY-MM-DD), defaults to today
            weeks: Number of weeks (default: 1, max: 4)
        """
        from garmin_mcp import get_client

        client = get_client()
        end = date.fromisoformat(end_date) if end_date else date.today()
        weeks = min(weeks, 4)

        results = []
        for w in range(weeks):
            week_end = end - timedelta(weeks=w)
            week_start = week_end - timedelta(days=week_end.weekday())
            week_end_date = week_start + timedelta(days=6)

            daily_data = []
            current = week_start
            while current <= week_end_date:
                d = current.isoformat()
                day: dict[str, Any] = {"date": d}

                try:
                    stats = client.get_stats(d)
                    day["stress_avg"] = stats.get("averageStressLevel")
                    day["body_battery_high"] = stats.get("bodyBatteryHighestValue")
                    day["body_battery_low"] = stats.get("bodyBatteryLowestValue")
                    day["resting_hr"] = stats.get("restingHeartRate")
                    day["steps"] = stats.get("totalSteps")
                except Exception:
                    pass

                try:
                    sleep = client.get_sleep_data(d)
                    if isinstance(sleep, dict):
                        day["sleep_score"] = sleep.get("sleepScores", {}).get("overall", {}).get("value")
                        day["sleep_duration_seconds"] = sleep.get("sleepTimeSeconds")
                except Exception:
                    pass

                daily_data.append(day)
                current += timedelta(days=1)

            # Compute weekly averages
            stress_vals = [d.get("stress_avg") for d in daily_data if d.get("stress_avg") is not None]
            sleep_scores = [d.get("sleep_score") for d in daily_data if d.get("sleep_score") is not None]
            rhr_vals = [d.get("resting_hr") for d in daily_data if d.get("resting_hr") is not None]

            results.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end_date.isoformat(),
                "avg_stress": round(sum(stress_vals) / len(stress_vals), 1) if stress_vals else None,
                "avg_sleep_score": round(sum(sleep_scores) / len(sleep_scores), 1) if sleep_scores else None,
                "avg_resting_hr": round(sum(rhr_vals) / len(rhr_vals), 1) if rhr_vals else None,
                "daily_data": daily_data,
            })

        return results

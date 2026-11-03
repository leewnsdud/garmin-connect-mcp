"""Body weight tools (weigh-ins and body composition)."""

from datetime import date as date_cls, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import today_str
from garmin_mcp.sanitize import strip_pii


def _range(end: str, days: int) -> tuple[str, str]:
    end_date = date_cls.fromisoformat(end)
    days = max(1, min(days, 366))
    return (end_date - timedelta(days=days - 1)).isoformat(), end_date.isoformat()


def _grams_to_kg(value: Any) -> float | None:
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    # Garmin reports weight in grams.
    return round(value / 1000, 1) if value > 300 else round(float(value), 1)


def _summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Newest-first weigh-ins with the latest value at the top level as weightKg."""
    weigh_ins = sorted(
        (e for e in entries if e.get("weightKg") is not None and e.get("date")),
        key=lambda e: e["date"],
        reverse=True,
    )
    latest = weigh_ins[0] if weigh_ins else None
    return {
        "weightKg": latest["weightKg"] if latest else None,
        "date": latest["date"] if latest else None,
        "weighIns": weigh_ins,
    }


def register(mcp: FastMCP):
    @mcp.tool()
    def get_weigh_ins(date: str = "", days: int = 30) -> dict[str, Any]:
        """Get body weight weigh-ins (scale or manual entries in Garmin Connect)
        for the `days` days ending on `date`. Returns the latest weight as
        `weightKg` plus every daily weigh-in, newest first, in kg.

        Args:
            date: End date (YYYY-MM-DD), defaults to today
            days: Number of days to look back (default: 30, max: 366)
        """
        from garmin_mcp import get_client

        client = get_client()
        start, end = _range(date or today_str(), days)
        raw = client.get_weigh_ins(start, end) or {}

        entries = []
        for day in raw.get("dailyWeightSummaries") or []:
            latest = day.get("latestWeight") or {}
            entries.append({
                "date": day.get("summaryDate") or latest.get("calendarDate"),
                "weightKg": _grams_to_kg(latest.get("weight")),
                "bmi": latest.get("bmi"),
                "bodyFatPercent": latest.get("bodyFat"),
                "source": latest.get("sourceType"),
            })
        return strip_pii(_summarize(entries))

    @mcp.tool()
    def get_body_composition(date: str = "", days: int = 30) -> dict[str, Any]:
        """Get body composition (weight, BMI, body fat, muscle mass) for the
        `days` days ending on `date`. Returns the latest weight as `weightKg`
        plus daily entries, newest first, in kg.

        Args:
            date: End date (YYYY-MM-DD), defaults to today
            days: Number of days to look back (default: 30, max: 366)
        """
        from garmin_mcp import get_client

        client = get_client()
        start, end = _range(date or today_str(), days)
        raw = client.get_body_composition(start, end) or {}

        entries = [
            {
                "date": item.get("calendarDate"),
                "weightKg": _grams_to_kg(item.get("weight")),
                "bmi": item.get("bmi"),
                "bodyFatPercent": item.get("bodyFat"),
                "muscleMassKg": _grams_to_kg(item.get("muscleMass")),
            }
            for item in raw.get("dateWeightList") or []
        ]
        return strip_pii(_summarize(entries))

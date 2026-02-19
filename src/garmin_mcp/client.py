"""Garmin API client wrapper with error handling."""

import re
import time
from datetime import date, datetime, timedelta
from typing import Any

from garminconnect import Garmin


DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date(date_str: str) -> str:
    """Validate date string format (YYYY-MM-DD)."""
    if not DATE_PATTERN.match(date_str):
        raise ValueError(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.")
    return date_str


def today_str() -> str:
    """Return today's date as YYYY-MM-DD string."""
    return date.today().isoformat()


class GarminClient:
    """Wrapper around garminconnect.Garmin with error handling and retry logic."""

    def __init__(self, garmin: Garmin):
        self._garmin = garmin

    def _call(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a Garmin API method with retry on rate limiting."""
        method = getattr(self._garmin, method_name)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                return method(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                # Rate limited - retry with backoff
                if "429" in error_str or "Too Many Requests" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        time.sleep(wait_time)
                        continue
                raise

    # --- Activities ---

    def get_activities(self, start: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        return self._call("get_activities", start, limit)

    def get_activities_by_date(
        self,
        start_date: str,
        end_date: str,
        activity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        validate_date(start_date)
        validate_date(end_date)
        return self._call(
            "get_activities_by_date",
            start_date,
            end_date,
            activity_type,
        )

    def get_activity(self, activity_id: int) -> dict[str, Any]:
        return self._call("get_activity", activity_id)

    def get_activity_splits(self, activity_id: int) -> dict[str, Any]:
        return self._call("get_activity_splits", activity_id)

    def get_activity_split_summaries(self, activity_id: int) -> dict[str, Any]:
        return self._call("get_activity_split_summaries", activity_id)

    def get_activity_hr_in_timezones(self, activity_id: int) -> list[dict[str, Any]]:
        return self._call("get_activity_hr_in_timezones", activity_id)

    def get_activity_weather(self, activity_id: int) -> dict[str, Any]:
        return self._call("get_activity_weather", activity_id)

    def get_activity_typed_splits(self, activity_id: int) -> dict[str, Any]:
        return self._call("get_activity_typed_splits", activity_id)

    # --- Training ---

    def get_training_status(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_training_status", date_str)

    def get_training_readiness(self, date_str: str) -> list[dict[str, Any]]:
        validate_date(date_str)
        return self._call("get_training_readiness", date_str)

    def get_max_metrics(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_max_metrics", date_str)

    def get_fitnessage_data(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_fitnessage_data", date_str)

    def get_race_predictions(self) -> dict[str, Any]:
        return self._call("get_race_predictions")

    def get_lactate_threshold(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if start_date:
            validate_date(start_date)
            kwargs["start_date"] = start_date
        if end_date:
            validate_date(end_date)
            kwargs["end_date"] = end_date
        return self._call("get_lactate_threshold", **kwargs)

    # --- Heart Rate ---

    def get_heart_rates(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_heart_rates", date_str)

    def get_rhr_day(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_rhr_day", date_str)

    def get_hrv_data(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_hrv_data", date_str)

    # --- Wellness ---

    def get_sleep_data(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_sleep_data", date_str)

    def get_stress_data(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_stress_data", date_str)

    def get_body_battery(self, start_date: str, end_date: str | None = None) -> list[dict[str, Any]]:
        validate_date(start_date)
        if end_date:
            validate_date(end_date)
        return self._call("get_body_battery", start_date, end_date)

    def get_spo2_data(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_spo2_data", date_str)

    def get_respiration_data(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_respiration_data", date_str)

    def get_stats(self, date_str: str) -> dict[str, Any]:
        validate_date(date_str)
        return self._call("get_stats", date_str)

    # --- Records & Goals ---

    def get_personal_record(self) -> list[dict[str, Any]]:
        return self._call("get_personal_record")

    def get_goals(self, status: str = "active") -> list[dict[str, Any]]:
        return self._call("get_goals", status)

    # --- Gear ---

    def get_profile_id(self) -> int:
        """Get the user's profile ID from garth profile data."""
        return self._garmin.garth.profile["profileId"]

    def get_gear(self, user_profile_number: int) -> list[dict[str, Any]]:
        return self._call("get_gear", user_profile_number)

    def get_gear_stats(self, gear_uuid: str) -> dict[str, Any]:
        return self._call("get_gear_stats", gear_uuid)

    # --- Workouts ---

    def get_workouts(self, start: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        return self._call("get_workouts", start, limit)

    def upload_running_workout(self, workout: Any) -> dict[str, Any]:
        return self._call("upload_running_workout", workout)

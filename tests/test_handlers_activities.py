#!/usr/bin/env python3
"""Tests covering handler logic in main.GarminConnectMCP."""

import unittest

from tests.helpers.stubs import ensure_test_stubs

ensure_test_stubs()

from main import GarminConnectMCP


class _FakeGarminClient:
    def __init__(self, activities):
        self._activities = activities
        self.calls = []

    def get_activities_by_date(self, start_date, end_date):
        self.calls.append((start_date, end_date))
        return self._activities


class _FakeGarminClientWithDirectDate:
    def __init__(self, activities):
        self._activities = activities
        self.calls = []

    def get_activities_for_date(self, date):
        self.calls.append(date)
        return self._activities


class ActivitiesHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_get_activities_for_date_filters_and_groups(self):
        server = GarminConnectMCP()
        fake_client = _FakeGarminClient(
            [
                {
                    "activityName": "Easy Run",
                    "distance": 5000,
                    "duration": 1500,
                    "activityType": {"typeKey": "running"},
                },
                {
                    "activityName": "Ride",
                    "distance": 20000,
                    "duration": 3600,
                    "activityType": {"typeKey": "cycling"},
                },
            ]
        )

        server.client_service._client = fake_client  # type: ignore[attr-defined]

        result = await server._get_activities_for_date({"date": "2024-01-15"})

        self.assertEqual(fake_client.calls, [("2024-01-15", "2024-01-15")])
        self.assertEqual(result["total_activities"], 2)
        self.assertEqual(len(result["running_activities"]), 1)
        self.assertEqual(len(result["other_activities"]), 1)
        self.assertAlmostEqual(result["summary"]["total_running_distance_km"], 5.0)
        self.assertAlmostEqual(result["summary"]["total_running_duration_minutes"], 25.0)

    async def test_get_activities_for_date_prefers_direct_method(self):
        server = GarminConnectMCP()
        fake_client = _FakeGarminClientWithDirectDate(
            [
                {
                    "activityName": "Tempo Run",
                    "distance": 10000,
                    "duration": 2400,
                    "activityType": {"typeKey": "running"},
                }
            ]
        )
        server.client_service._client = fake_client  # type: ignore[attr-defined]

        result = await server._get_activities_for_date({"date": "2024-02-01"})

        self.assertEqual(fake_client.calls, ["2024-02-01"])
        self.assertEqual(result["total_activities"], 1)
        self.assertEqual(len(result["running_activities"]), 1)


if __name__ == "__main__":
    unittest.main()


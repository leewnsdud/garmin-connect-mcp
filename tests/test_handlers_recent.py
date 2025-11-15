#!/usr/bin/env python3
"""Tests for recent running activities handler."""

import unittest

from tests.helpers.stubs import ensure_test_stubs

ensure_test_stubs()

from main import GarminConnectMCP  # noqa: E402
from utils import _cache  # noqa: E402


class _FakeRecentClient:
    def __init__(self, activities):
        self.activities = activities
        self.calls = []

    def get_activities_by_date(self, start_date, end_date):
        self.calls.append((start_date, end_date))
        return self.activities


class RecentActivitiesHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        _cache.clear()

    async def test_recent_running_activities_filters_and_paginates(self):
        server = GarminConnectMCP()
        fake_client = _FakeRecentClient(
            [
                {
                    "activityName": "Run 1",
                    "distance": 8000,
                    "duration": 2100,
                    "activityType": {"typeKey": "running"},
                },
                {
                    "activityName": "Morning Ride",
                    "distance": 20000,
                    "duration": 3600,
                    "activityType": {"typeKey": "cycling"},
                },
                {
                    "activityName": "Run 2",
                    "distance": 5000,
                    "duration": 1500,
                    "activityType": {"typeKey": "running"},
                },
            ]
        )
        server.client_service._client = fake_client  # type: ignore[attr-defined]

        result = await server._get_recent_running_activities({"limit": 1, "days_back": 30})

        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["activityName"], "Run 1")
        self.assertTrue(result["pagination"]["hasMore"])
        self.assertIn("nextCursor", result["pagination"])
        self.assertEqual(result["resources"]["complete_list"], "activity://list")
        self.assertEqual(len(fake_client.calls), 1)


if __name__ == "__main__":
    unittest.main()


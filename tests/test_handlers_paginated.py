#!/usr/bin/env python3
"""Tests for paginated activities handler."""

import unittest

from tests.helpers.stubs import ensure_test_stubs
from utils import _cache

ensure_test_stubs()

from main import GarminConnectMCP  # noqa: E402


class _FakePaginatedClient:
    def __init__(self, activities):
        self.activities = activities
        self.calls = []

    def get_activities(self, start, limit, activity_type):
        self.calls.append((start, limit, activity_type))
        return self.activities


class PaginatedActivitiesHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        _cache.clear()

    async def test_paginated_activities_default_running_filter(self):
        server = GarminConnectMCP()
        fake_client = _FakePaginatedClient(
            [
                {
                    "activityName": "Run 1",
                    "activityType": {"typeKey": "running"},
                    "distance": 5000,
                },
                {
                    "activityName": "Ride",
                    "activityType": {"typeKey": "cycling"},
                    "distance": 20000,
                },
            ]
        )
        server.client_service._client = fake_client  # type: ignore[attr-defined]

        result = await server._get_paginated_activities({"limit": 2, "start": 0})

        self.assertEqual(fake_client.calls, [(0, 2, "running")])
        self.assertEqual(len(result["activities"]), 1)
        self.assertEqual(result["activities"][0]["activityName"], "Run 1")
        self.assertFalse(result["pagination"]["has_more"])

    async def test_paginated_activities_all_types(self):
        server = GarminConnectMCP()
        fake_client = _FakePaginatedClient(
            [
                {"activityName": "Run 1", "activityType": {"typeKey": "running"}},
                {"activityName": "Ride", "activityType": {"typeKey": "cycling"}},
            ]
        )
        server.client_service._client = fake_client  # type: ignore[attr-defined]

        result = await server._get_paginated_activities(
            {"limit": 2, "start": 5, "activity_type": "all"}
        )

        self.assertEqual(fake_client.calls, [(5, 2, None)])
        self.assertEqual(len(result["activities"]), 2)
        self.assertTrue(result["pagination"]["has_more"])


if __name__ == "__main__":
    unittest.main()


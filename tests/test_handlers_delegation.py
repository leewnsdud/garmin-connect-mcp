#!/usr/bin/env python3
"""Tests for handlers that delegate to training/analytics modules."""

import unittest
from unittest.mock import AsyncMock, patch

from tests.helpers.stubs import ensure_test_stubs
from utils import _cache

ensure_test_stubs()

from main import GarminConnectMCP  # noqa: E402


class DelegationHandlersTestCase(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        _cache.clear()

    @patch("main.training_handlers.list_training_plans", new_callable=AsyncMock)
    async def test_list_training_plans_delegates(self, mock_handler):
        server = GarminConnectMCP()
        mock_handler.return_value = {"plans": []}

        args = {"goal_distance": "marathon"}
        result = await server._list_training_plans(args)

        mock_handler.assert_awaited_once_with(server.client_service, args)
        self.assertEqual(result, {"plans": []})

    @patch("main.training_handlers.get_training_plan_overview", new_callable=AsyncMock)
    async def test_training_plan_overview_delegates(self, mock_handler):
        server = GarminConnectMCP()
        mock_handler.return_value = {"overview": "data"}

        args = {"plan_id": "123", "schedule_weeks": 3}
        result = await server._get_training_plan_overview(args)

        mock_handler.assert_awaited_once_with(server.client_service, args)
        self.assertEqual(result, {"overview": "data"})

    @patch("main.training_handlers.get_training_plan_schedule", new_callable=AsyncMock)
    async def test_training_plan_schedule_delegates(self, mock_handler):
        server = GarminConnectMCP()
        mock_handler.return_value = {"schedule": []}

        args = {"plan_id": "456", "weeks": 8}
        result = await server._get_training_plan_schedule(args)

        mock_handler.assert_awaited_once_with(server.client_service, args)
        self.assertEqual(result, {"schedule": []})

    @patch("main.analytics_handlers.get_gear_insights", new_callable=AsyncMock)
    async def test_gear_insights_delegates(self, mock_handler):
        server = GarminConnectMCP()
        mock_handler.return_value = {"gear": []}

        args = {"distance_threshold_km": 700}
        result = await server._get_gear_insights(args)

        mock_handler.assert_awaited_once_with(server.client_service, args)
        self.assertEqual(result, {"gear": []})


if __name__ == "__main__":
    unittest.main()


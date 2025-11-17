#!/usr/bin/env python3
"""Tests for weekly running summary handler."""

import unittest
from unittest.mock import AsyncMock, patch

from tests.helpers.stubs import ensure_test_stubs

ensure_test_stubs()

from main import GarminConnectMCP  # noqa: E402


class WeeklySummaryHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    @patch("main.analytics_handlers.get_weekly_running_summary", new_callable=AsyncMock)
    async def test_weekly_summary_delegates_to_analytics_handler(self, summary_mock):
        server = GarminConnectMCP()
        summary_mock.return_value = {"weekly": [{"distance": 50}]}

        args = {"weeks_back": 2}
        result = await server._get_weekly_running_summary(args)

        summary_mock.assert_awaited_once_with(
            server.client_service, args, timezone=server.timezone
        )
        self.assertEqual(result, {"weekly": [{"distance": 50}]})


if __name__ == "__main__":
    unittest.main()


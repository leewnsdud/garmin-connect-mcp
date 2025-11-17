#!/usr/bin/env python3
"""Unit tests for response size guard utilities."""

import unittest

from utils import split_large_response


class ResponseGuardUtilsTestCase(unittest.TestCase):
    def test_split_moves_large_field_without_name_hint(self) -> None:
        """Ensure arbitrary large fields are moved to overflow resources."""
        stored_payloads = {}

        def fake_resource_callback(field: str, value):
            stored_payloads[field] = value
            return f"overflow://{field}"

        data = {
            "metadata": {"type": "tcx"},
            "data": "X" * 150_000,  # large blob without special field name
        }

        result = split_large_response(
            data, max_size_bytes=10_000, create_resource_callback=fake_resource_callback
        )

        self.assertIn("data_resource", result)
        self.assertIn("_overflow_info", result)
        self.assertEqual(result["_overflow_info"]["fields_moved"], ["data"])
        self.assertEqual(stored_payloads["data"], data["data"])

    def test_split_full_response_fallback(self) -> None:
        """When many tiny fields still exceed limit, entire payload is offloaded."""
        calls = []

        def fake_resource_callback(field: str, value):
            calls.append((field, len(value) if isinstance(value, str) else None))
            return f"overflow://{field}_{len(calls)}"

        data = {f"field_{i}": "x" * 500 for i in range(3000)}  # thousands of tiny fields

        result = split_large_response(
            data, max_size_bytes=20_000, create_resource_callback=fake_resource_callback
        )

        self.assertIn("overflow_resource", result)
        self.assertIn("__full_response__", result["_overflow_info"]["fields_moved"])
        self.assertTrue(result["_overflow_info"]["resource_only"])
        self.assertIn("summary", result)
        self.assertLessEqual(
            len(result["summary"]["available_fields"]),
            50,
        )
        self.assertGreater(result["summary"]["total_available_fields"], 50)
        self.assertGreaterEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()


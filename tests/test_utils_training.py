#!/usr/bin/env python3
"""Unit tests for training-related utility helpers."""

import unittest

from utils import (
    build_training_plan_schedule_preview,
    normalize_distance_to_km,
    summarize_training_plan_detail,
    summarize_training_plans,
)


class TrainingUtilsTestCase(unittest.TestCase):
    def test_normalize_distance_to_km(self) -> None:
        self.assertEqual(normalize_distance_to_km(5000), 5.0)
        self.assertEqual(normalize_distance_to_km(42.195), 42.2)
        self.assertEqual(normalize_distance_to_km({"distanceMeters": 10000}), 10.0)
        self.assertIsNone(normalize_distance_to_km(None))

    def test_summarize_training_plans_filters(self) -> None:
        plans_response = {
            "trainingPlanList": [
                {
                    "trainingPlanId": 1,
                    "name": "10K Beginner",
                    "primarySport": "running",
                    "distanceType": "10K",
                    "experienceLevel": "beginner",
                    "durationWeeks": 8,
                },
                {
                    "trainingPlanId": 2,
                    "name": "Cycling Base",
                    "primarySport": "cycling",
                    "distanceType": "40K",
                    "experienceLevel": "beginner",
                    "durationWeeks": 6,
                },
            ]
        }

        result = summarize_training_plans(
            plans_response,
            goal_distance="10k",
            experience_level="beginner",
            max_items=5,
        )

        self.assertEqual(result["total_available"], 1)
        self.assertEqual(len(result["plans"]), 1)
        self.assertEqual(result["plans"][0]["name"], "10K Beginner")

    def test_summarize_training_plan_detail_with_schedule(self) -> None:
        plan_detail = {
            "planSummary": {
                "trainingPlanId": 100,
                "planName": "Half Marathon",
                "goalType": "TIME_GOAL",
                "distanceType": "half_marathon",
                "experienceLevel": "intermediate",
                "durationWeeks": 12,
                "eventDate": "2025-04-13",
            },
            "phases": [
                {"phaseName": "Base", "numberOfWeeks": 4, "description": "base"},
                {"phaseName": "Build", "numberOfWeeks": 4, "description": "build"},
            ],
            "trainingPlanWeekSummaries": [
                {
                    "weekNumber": 1,
                    "focus": "Base",
                    "plannedDistance": 45000,
                    "keyWorkouts": [
                        {"workoutName": "롱런", "plannedDistance": 18000},
                        {"workoutName": "템포", "plannedDistance": 10000},
                    ],
                }
            ],
        }

        overview = summarize_training_plan_detail(plan_detail, schedule_weeks=2)
        self.assertEqual(overview["plan"]["name"], "Half Marathon")
        self.assertEqual(len(overview["phases"]), 2)
        self.assertEqual(overview["schedule_preview"]["weeks"][0]["planned_distance_km"], 45.0)

    def test_build_training_plan_schedule_preview_grouping(self) -> None:
        plan_detail = {
            "trainingPlanWorkouts": [
                {
                    "trainingPlanWeek": 1,
                    "workoutName": "롱런",
                    "plannedDistanceMeters": 18000,
                },
                {
                    "trainingPlanWeek": 1,
                    "workoutName": "인터벌",
                    "plannedDistance": 10000,
                },
                {
                    "trainingPlanWeek": 2,
                    "workoutName": "롱런",
                    "plannedDistanceMeters": 20000,
                },
            ]
        }

        schedule = build_training_plan_schedule_preview(plan_detail, weeks=2)
        self.assertEqual(schedule["weeks"][0]["week"], 1)
        self.assertEqual(schedule["weeks"][0]["total_workouts"], 2)
        self.assertAlmostEqual(schedule["weeks"][0]["planned_distance_km"], 28.0)
        self.assertEqual(len(schedule["weeks"]), 2)


if __name__ == "__main__":
    unittest.main()

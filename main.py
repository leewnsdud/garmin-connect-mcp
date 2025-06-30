#!/usr/bin/env python3
import asyncio
import logging
import os
from calendar import monthrange
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from garminconnect import Garmin
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv

# Import utility functions and decorators
from utils import (
    handle_api_errors, validate_required_params, with_retry, cached,
    filter_running_activities, format_time, format_pace, parse_time,
    meters_per_second_to_pace, calculate_vdot_from_time,
    calculate_training_paces_from_vdot, clear_cache, get_cache_stats,
    DEFAULT_MAX_HR, RUNNING_ACTIVITY_TYPES, DISTANCE_TYPE_IDS,
    DISTANCE_METERS, GarminAPIError
)

load_dotenv()

logger = logging.getLogger(__name__)

class GarminConnectMCP:
    def __init__(self):
        self.garmin_client: Optional[Garmin] = None
        self.server = Server("garmin-connect-mcp")
        self.tool_handlers: Dict[str, Any] = {}
        self._setup_tools()
        self._setup_tool_handlers()
    
    def _setup_tool_handlers(self):
        """Set up dictionary-based tool handler mapping."""
        self.tool_handlers = {
            "get_personal_records": self._get_personal_records,
            "get_vo2max": self._get_vo2max,
            "get_training_status": self._get_training_status,
            "get_recent_running_activities": self._get_recent_running_activities,
            "get_activity_summary": self._get_activity_summary,
            "get_activity_details": self._get_activity_details,
            "get_heart_rate_metrics": self._get_heart_rate_metrics,
            "get_sleep_analysis": self._get_sleep_analysis,
            "get_body_battery": self._get_body_battery,
            "get_stress_levels": self._get_stress_levels,
            "get_daily_activity": self._get_daily_activity,
            "calculate_training_paces": self._calculate_training_paces,
            "get_advanced_running_metrics": self._get_advanced_running_metrics,
            "analyze_heart_rate_zones": self._analyze_heart_rate_zones,
            "set_race_goal": self._set_race_goal,
            "analyze_training_load": self._analyze_training_load,
            "get_running_trends": self._get_running_trends,
            "get_lactate_threshold": self._get_lactate_threshold,
            "get_race_predictions": self._get_race_predictions,
            "get_training_readiness": self._get_training_readiness,
            "get_recovery_time": self._get_recovery_time,
            "get_training_load_balance": self._get_training_load_balance,
            "get_training_effect": self._get_training_effect,
            "calculate_vdot_zones": self._calculate_vdot_zones,
            "analyze_threshold_zones": self._analyze_threshold_zones,
            "suggest_daily_workout": self._suggest_daily_workout,
            "analyze_workout_quality": self._analyze_workout_quality
        }

    def _setup_tools(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="get_personal_records",
                    description="Get personal best times for running distances (5K, 10K, half marathon, full marathon)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "distances": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Running distances to get records for",
                                "default": ["5K", "10K", "half_marathon", "marathon"]
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_vo2max",
                    description="Get current VO2 Max value and historical data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_training_status",
                    description="Get current training status including training effect, load balance, and fitness trends",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_recent_running_activities",
                    description="Get recent running activities with detailed metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of activities to retrieve",
                                "default": 20
                            },
                            "days_back": {
                                "type": "integer", 
                                "description": "Number of days back to search",
                                "default": 30
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_activity_summary",
                    description="Get basic activity information including distance, time, pace, and elevation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "activity_id": {
                                "type": "string",
                                "description": "Garmin activity ID",
                                "required": True
                            }
                        },
                        "required": ["activity_id"]
                    }
                ),
                types.Tool(
                    name="get_activity_details",
                    description="Get comprehensive activity metrics including splits, advanced metrics, and performance data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "activity_id": {
                                "type": "string",
                                "description": "Garmin activity ID",
                                "required": True
                            }
                        },
                        "required": ["activity_id"]
                    }
                ),
                types.Tool(
                    name="get_heart_rate_metrics",
                    description="Get heart rate metrics including resting heart rate and heart rate variability (HRV)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_sleep_analysis",
                    description="Get detailed sleep data including sleep stages, quality, and duration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_body_battery",
                    description="Get body battery energy levels throughout the day",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_stress_levels",
                    description="Get stress level data and analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_daily_activity",
                    description="Get daily activity metrics including steps, floors climbed, and intensity minutes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="calculate_training_paces",
                    description="Calculate Jack Daniels training paces based on recent race performance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "race_distance": {
                                "type": "string",
                                "description": "Recent race distance (5K, 10K, half_marathon, marathon)",
                                "required": True
                            },
                            "race_time": {
                                "type": "string",
                                "description": "Race time in HH:MM:SS format",
                                "required": True
                            }
                        },
                        "required": ["race_distance", "race_time"]
                    }
                ),
                types.Tool(
                    name="get_advanced_running_metrics",
                    description="Get advanced running metrics including stride length, vertical ratio, vertical amplitude, ground contact time",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "activity_id": {
                                "type": "string",
                                "description": "Garmin activity ID",
                                "required": True
                            }
                        },
                        "required": ["activity_id"]
                    }
                ),
                types.Tool(
                    name="analyze_heart_rate_zones",
                    description="Analyze heart rate zone distribution and time spent in each zone for an activity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "activity_id": {
                                "type": "string",
                                "description": "Garmin activity ID",
                                "required": True
                            }
                        },
                        "required": ["activity_id"]
                    }
                ),
                types.Tool(
                    name="set_race_goal",
                    description="Set a target race goal and track progress",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "race_distance": {
                                "type": "string",
                                "description": "Target race distance (5K, 10K, half_marathon, marathon)",
                                "required": True
                            },
                            "target_time": {
                                "type": "string",
                                "description": "Target race time in HH:MM:SS format",
                                "required": True
                            },
                            "race_date": {
                                "type": "string",
                                "description": "Target race date in YYYY-MM-DD format",
                                "required": True
                            }
                        },
                        "required": ["race_distance", "target_time", "race_date"]
                    }
                ),
                types.Tool(
                    name="analyze_training_load",
                    description="Analyze training load and recovery status to prevent injury",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "weeks_back": {
                                "type": "integer",
                                "description": "Number of weeks to analyze",
                                "default": 4
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_running_trends",
                    description="Get running performance trends over a specified period",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "months_back": {
                                "type": "integer",
                                "description": "Number of months to analyze",
                                "default": 6
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_lactate_threshold",
                    description="Get lactate threshold pace and heart rate data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_race_predictions",
                    description="Get predicted race times based on current fitness level",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="get_training_readiness",
                    description="Get training readiness score and recommendations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format, defaults to today",
                                "default": datetime.now().strftime("%Y-%m-%d")
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_recovery_time",
                    description="Get recommended recovery time after recent activities",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="get_training_load_balance",
                    description="Get acute vs chronic training load balance (ATL/CTL ratio) for injury prevention",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "weeks_back": {
                                "type": "integer",
                                "description": "Number of weeks to analyze for training load",
                                "default": 6
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_training_effect",
                    description="Get aerobic and anaerobic training effect analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days_back": {
                                "type": "integer",
                                "description": "Number of days to analyze",
                                "default": 7
                            }
                        }
                    }
                ),
                types.Tool(
                    name="calculate_vdot_zones",
                    description="Calculate VDOT and training zones based on recent race performance or time trial",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "race_distance": {
                                "type": "string",
                                "description": "Race distance (5K, 10K, half_marathon, marathon)",
                                "required": True
                            },
                            "race_time": {
                                "type": "string",
                                "description": "Race time in HH:MM:SS format",
                                "required": True
                            }
                        },
                        "required": ["race_distance", "race_time"]
                    }
                ),
                types.Tool(
                    name="analyze_threshold_zones",
                    description="Analyze lactate threshold zones for double threshold training",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="suggest_daily_workout",
                    description="Suggest appropriate workout based on current condition and training phase",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "training_phase": {
                                "type": "string",
                                "description": "Current training phase (base, build, peak, taper, recovery)",
                                "default": "build"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="analyze_workout_quality",
                    description="Analyze how well a workout was executed compared to plan",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "activity_id": {
                                "type": "string",
                                "description": "Garmin activity ID to analyze",
                                "required": True
                            },
                            "planned_workout": {
                                "type": "object",
                                "description": "Details of what was planned",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "description": "Workout type (easy, tempo, interval, long)"
                                    },
                                    "target_pace": {
                                        "type": "string",
                                        "description": "Target pace per km (MM:SS)"
                                    },
                                    "target_distance": {
                                        "type": "number",
                                        "description": "Target distance in km"
                                    }
                                }
                            }
                        },
                        "required": ["activity_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent]:
            if not self.garmin_client:
                await self._authenticate()
            
            try:
                # Use dictionary-based dispatch for tool handling
                handler = self.tool_handlers.get(name)
                if not handler:
                    raise ValueError(f"Unknown tool: {name}")
                
                result = await handler(arguments or {})
                return [types.TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    @with_retry(max_attempts=3, delay=2.0)
    async def _authenticate(self):
        username = os.getenv("GARMIN_USERNAME")
        password = os.getenv("GARMIN_PASSWORD")
        
        if not username or not password:
            raise ValueError(
                "Authentication failed. Please ensure GARMIN_USERNAME and GARMIN_PASSWORD are set in environment variables."
            )
        
        self.garmin_client = Garmin(email=username, password=password)
        
        # Try to login with stored tokens first
        tokenstore = os.path.expanduser("~/.garminconnect")
        try:
            result = await asyncio.to_thread(self.garmin_client.login, tokenstore)
            logger.info("Successfully authenticated with stored tokens")
        except Exception as token_error:
            logger.info(f"Token login failed: {token_error}")
            # Fallback to credential login
            try:
                result = await asyncio.to_thread(self.garmin_client.login)
                if result is True or isinstance(result, tuple):
                    logger.info("Successfully authenticated with credentials")
                elif isinstance(result, dict):
                    raise ValueError("Multi-factor authentication required. Please disable 2FA temporarily or use setup script.")
                else:
                    raise ValueError(f"Unexpected login result: {result}")
            except Exception as cred_error:
                logger.error(f"Credential login failed: {cred_error}")
                raise cred_error

    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_personal_records(self, args: Dict[str, Any]) -> Dict[str, Any]:
        distances = args.get("distances", ["5K", "10K", "half_marathon", "marathon"])
        
        # Get actual personal records from Garmin Connect
        try:
            personal_records_data = await asyncio.to_thread(self.garmin_client.get_personal_record)
        except Exception as e:
            logger.warning(f"Failed to get personal records: {e}")
            personal_records_data = None
        
        # Process personal records data
        formatted_records = {}
        if personal_records_data:
            # Extract running-specific records
            for record in personal_records_data:
                if isinstance(record, dict):
                    activity_type = record.get('activityType', '')
                    if activity_type and ('running' in activity_type.lower() or activity_type in RUNNING_ACTIVITY_TYPES):
                        type_id = record.get('typeId')
                        value = record.get('value')
                        pr_date = record.get('activityStartDateTimeLocalFormatted', record.get('prStartTimeLocalFormatted'))
                        activity_id = record.get('activityId')
                        
                        # Map typeId to readable distances
                        # Based on Garmin's typeId mapping for running PRs
                        
                        if type_id in DISTANCE_TYPE_IDS:
                            distance_key = DISTANCE_TYPE_IDS[type_id]
                            # Convert time value (in seconds) to HH:MM:SS format
                            if value and isinstance(value, (int, float)):
                                time_str = format_time(value)
                                
                                formatted_records[distance_key] = {
                                    'time': time_str,
                                    'seconds': value,
                                    'date': pr_date,
                                    'activity_id': activity_id
                                }
        
        return {
            "personal_records": formatted_records if formatted_records else {
                "note": "No personal records found. Records will be created as you complete activities.",
                "raw_data": personal_records_data
            }
        }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_vo2max(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # Get VO2 Max data
        try:
            vo2_max_data = await asyncio.to_thread(self.garmin_client.get_max_metrics, date)
            # Extract VO2 Max value if available
            vo2_max_value = None
            vo2_max_trend = None
            
            if isinstance(vo2_max_data, list) and len(vo2_max_data) > 0:
                for metric in vo2_max_data:
                    if 'generic' in metric and 'maxMet' in metric['generic']:
                        vo2_max_value = metric['generic']['maxMet']
                        # Check for trend data
                        if 'fitnessTrendData' in metric:
                            vo2_max_trend = metric['fitnessTrendData']
                        break
            
            # Get race predictions based on VO2 Max
            race_predictions = None
            try:
                race_predictions = await asyncio.to_thread(self.garmin_client.get_race_predictions)
            except:
                pass
            
            return {
                "vo2_max": vo2_max_value,
                "vo2_max_trend": vo2_max_trend,
                "race_predictions": race_predictions,
                "date": date,
                "raw_data": vo2_max_data
            }
        except Exception as e:
            logger.error(f"Failed to get VO2 Max data: {e}")
            return {
                "error": f"Failed to get VO2 Max data: {str(e)}",
                "date": date
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_training_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # Get training status
        try:
            training_status = await asyncio.to_thread(self.garmin_client.get_training_status, date)
        except Exception as e:
            logger.error(f"Failed to get training status: {e}")
            training_status = None
        
        # Get training readiness
        try:
            training_readiness = await asyncio.to_thread(self.garmin_client.get_training_readiness, date)
        except:
            training_readiness = None
        
        # Extract key training metrics
        status_summary = {}
        if training_status:
            status_summary = {
                "status": training_status.get('trainingStatusType', 'Unknown'),
                "fitness_level": training_status.get('fitnessLevel'),
                "load_balance": training_status.get('loadBalance'),
                "recovery_time": training_status.get('recoveryTime'),
                "training_effect": {
                    "aerobic": training_status.get('lastWorkoutAerobicTrainingEffect'),
                    "anaerobic": training_status.get('lastWorkoutAnaerobicTrainingEffect')
                }
            }
        
        return {
            "training_status": status_summary,
            "training_readiness": training_readiness,
            "date": date,
            "raw_training_status": training_status,
            "raw_training_readiness": training_readiness
        }

    @handle_api_errors
    async def _get_recent_running_activities(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        limit = args.get("limit", 20)
        days_back = args.get("days_back", 30)
        
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        activities = await asyncio.to_thread(
            self.garmin_client.get_activities_by_date, start_date, end_date
        )
        
        # Filter for running activities only
        running_activities = filter_running_activities(activities[:limit])
        
        return running_activities

    @handle_api_errors
    @validate_required_params("activity_id")
    async def _get_activity_summary(self, args: Dict[str, Any]) -> Dict[str, Any]:
        activity_id = args["activity_id"]
        
        # Get basic activity data
        activity_basic = await asyncio.to_thread(
            self.garmin_client.get_activity, activity_id
        )
        
        # Extract key summary metrics
        summary = {
            "activity_id": activity_id,
            "activity_name": activity_basic.get("activityName"),
            "activity_type": activity_basic.get("activityType", {}).get("typeKey"),
            "start_time": activity_basic.get("startTimeLocal"),
            "distance_km": round(activity_basic.get("distance", 0) / 1000, 2) if activity_basic.get("distance") else 0,
            "duration_seconds": activity_basic.get("duration"),
            "duration_formatted": activity_basic.get("durationFormatted"),
            "average_pace_per_km": activity_basic.get("averagePaceInMinutesPerKilometer"),
            "average_speed_kmh": round(activity_basic.get("averageSpeed", 0) * 3.6, 2) if activity_basic.get("averageSpeed") else 0,
            "elevation_gain_m": activity_basic.get("elevationGain"),
            "elevation_loss_m": activity_basic.get("elevationLoss"),
            "calories": activity_basic.get("calories"),
            "average_hr": activity_basic.get("averageHR"),
            "max_hr": activity_basic.get("maxHR"),
            "training_effect": {
                "aerobic": activity_basic.get("aerobicTrainingEffect"),
                "anaerobic": activity_basic.get("anaerobicTrainingEffect")
            }
        }
        
        return summary
    
    @handle_api_errors
    @validate_required_params("activity_id")
    async def _get_activity_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        activity_id = args["activity_id"]
        
        # Get detailed activity data
        try:
            activity_details = await asyncio.to_thread(
                self.garmin_client.get_activity_details, activity_id
            )
        except Exception as e:
            logger.error(f"Failed to get activity details: {e}")
            activity_details = {}
        
        # Get splits data
        try:
            splits = await asyncio.to_thread(
                self.garmin_client.get_activity_splits, activity_id
            )
        except:
            splits = None
        
        # Get weather data
        try:
            weather = await asyncio.to_thread(
                self.garmin_client.get_activity_weather, activity_id
            )
        except:
            weather = None
        
        # Extract comprehensive metrics
        return {
            "activity_id": activity_id,
            "detailed_metrics": activity_details,
            "splits": splits,
            "weather": weather,
            "performance_metrics": {
                "normalized_power": activity_details.get("summaryDTO", {}).get("normalizedPower"),
                "training_stress_score": activity_details.get("summaryDTO", {}).get("trainingStressScore"),
                "intensity_factor": activity_details.get("summaryDTO", {}).get("intensityFactor"),
                "stamina": activity_details.get("summaryDTO", {}).get("stamina"),
                "estimated_race_predictor": activity_details.get("summaryDTO", {}).get("estimatedRacePredictor")
            },
            "gps_data_available": activity_details.get("metricDescriptors", []) != [],
            "note": "Use analyze_heart_rate_zones for heart rate zone analysis"
        }

    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_heart_rate_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # Get resting heart rate data
        rhr_data = await asyncio.to_thread(self.garmin_client.get_rhr_day, date)
        
        # Extract actual RHR value
        rhr_value = None
        if rhr_data and isinstance(rhr_data, dict):
            all_metrics = rhr_data.get('allMetrics', {})
            metrics_map = all_metrics.get('metricsMap', {})
            if 'WELLNESS_RESTING_HEART_RATE' in metrics_map:
                rhr_list = metrics_map['WELLNESS_RESTING_HEART_RATE']
                if rhr_list and len(rhr_list) > 0:
                    rhr_value = rhr_list[0].get('value')
        
        # Get heart rate zones configuration
        try:
            hr_zones = await asyncio.to_thread(self.garmin_client.get_heart_rate_zones)
        except:
            hr_zones = None
        
        # Get HRV data if available
        hrv_data = None
        try:
            # HRV might be in stress data or separate endpoint
            stress_data = await asyncio.to_thread(self.garmin_client.get_stress_data, date)
            if stress_data and isinstance(stress_data, list):
                # Extract HRV from stress data if available
                for entry in stress_data:
                    if 'hrv' in entry:
                        hrv_data = entry['hrv']
                        break
        except:
            pass
        
        return {
            "date": date,
            "resting_heart_rate": rhr_value,
            "heart_rate_zones": hr_zones,
            "hrv": hrv_data,
            "rhr_raw_data": rhr_data
        }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_sleep_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        try:
            sleep_data = await asyncio.to_thread(self.garmin_client.get_sleep_data, date)
            
            # Process sleep data for easier consumption
            sleep_summary = {}
            if sleep_data:
                sleep_summary = {
                    "total_sleep_hours": round(sleep_data.get('sleepTimeSeconds', 0) / 3600, 2) if sleep_data.get('sleepTimeSeconds') else 0,
                    "sleep_start": sleep_data.get('sleepStartTimestampLocal'),
                    "sleep_end": sleep_data.get('sleepEndTimestampLocal'),
                    "sleep_levels": {
                        "deep": sleep_data.get('deepSleepSeconds', 0),
                        "light": sleep_data.get('lightSleepSeconds', 0),
                        "rem": sleep_data.get('remSleepSeconds', 0),
                        "awake": sleep_data.get('awakeSleepSeconds', 0)
                    },
                    "sleep_score": sleep_data.get('sleepScore'),
                    "sleep_quality": sleep_data.get('sleepQuality')
                }
            
            return {
                "date": date,
                "sleep_summary": sleep_summary,
                "raw_sleep_data": sleep_data
            }
        except Exception as e:
            logger.error(f"Failed to get sleep data: {e}")
            return {
                "date": date,
                "error": f"Failed to get sleep data: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_body_battery(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        try:
            body_battery = await asyncio.to_thread(self.garmin_client.get_body_battery, date)
            
            # Extract key body battery metrics
            battery_summary = {}
            if body_battery and isinstance(body_battery, list) and len(body_battery) > 0:
                latest = body_battery[-1]  # Get most recent reading
                battery_summary = {
                    "current_level": latest.get('level'),
                    "charged_value": latest.get('charged'),
                    "drained_value": latest.get('drained')
                }
            
            return {
                "date": date,
                "body_battery_summary": battery_summary,
                "body_battery_timeline": body_battery
            }
        except Exception as e:
            logger.error(f"Failed to get body battery data: {e}")
            return {
                "date": date,
                "error": f"Failed to get body battery data: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_stress_levels(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        try:
            stress_data = await asyncio.to_thread(self.garmin_client.get_stress_data, date)
            
            # Process stress data
            stress_summary = {}
            if stress_data and isinstance(stress_data, list):
                # Calculate average stress
                stress_values = [s.get('value', 0) for s in stress_data if s.get('value')]
                if stress_values:
                    stress_summary = {
                        "average_stress": round(sum(stress_values) / len(stress_values), 1),
                        "max_stress": max(stress_values),
                        "min_stress": min(stress_values),
                        "current_stress": stress_values[-1] if stress_values else None
                    }
            
            return {
                "date": date,
                "stress_summary": stress_summary,
                "stress_timeline": stress_data
            }
        except Exception as e:
            logger.error(f"Failed to get stress data: {e}")
            return {
                "date": date,
                "error": f"Failed to get stress data: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_daily_activity(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # Get various daily activity metrics
        try:
            steps_data = await asyncio.to_thread(self.garmin_client.get_steps_data, date)
        except:
            steps_data = None
        
        try:
            floors_data = await asyncio.to_thread(self.garmin_client.get_floors, date)
        except:
            floors_data = None
        
        try:
            intensity_data = await asyncio.to_thread(self.garmin_client.get_intensity_minutes_data, date)
        except:
            intensity_data = None
        
        # Get daily stats summary
        try:
            daily_stats = await asyncio.to_thread(self.garmin_client.get_stats, date)
        except:
            daily_stats = None
        
        # Process and summarize daily activity
        activity_summary = {
            "steps": None,
            "floors_climbed": None,
            "intensity_minutes": {
                "moderate": None,
                "vigorous": None
            },
            "calories_burned": None,
            "distance_km": None
        }
        
        if steps_data:
            # Handle both list and dict responses
            if isinstance(steps_data, list) and len(steps_data) > 0:
                activity_summary["steps"] = steps_data[0].get('totalSteps') if steps_data[0] else None
            elif isinstance(steps_data, dict):
                activity_summary["steps"] = steps_data.get('totalSteps')
        
        if floors_data:
            # Handle both list and dict responses
            if isinstance(floors_data, list) and len(floors_data) > 0:
                activity_summary["floors_climbed"] = floors_data[0].get('floorsClimbed') if floors_data[0] else None
            elif isinstance(floors_data, dict):
                activity_summary["floors_climbed"] = floors_data.get('floorsClimbed')
        
        if intensity_data:
            # Handle both list and dict responses
            if isinstance(intensity_data, list) and len(intensity_data) > 0:
                activity_summary["intensity_minutes"]["moderate"] = intensity_data[0].get('moderateIntensityMinutes') if intensity_data[0] else None
                activity_summary["intensity_minutes"]["vigorous"] = intensity_data[0].get('vigorousIntensityMinutes') if intensity_data[0] else None
            elif isinstance(intensity_data, dict):
                activity_summary["intensity_minutes"]["moderate"] = intensity_data.get('moderateIntensityMinutes')
                activity_summary["intensity_minutes"]["vigorous"] = intensity_data.get('vigorousIntensityMinutes')
        
        if daily_stats:
            # Handle both list and dict responses
            if isinstance(daily_stats, list) and len(daily_stats) > 0:
                activity_summary["calories_burned"] = daily_stats[0].get('totalKilocalories') if daily_stats[0] else None
                activity_summary["distance_km"] = round(daily_stats[0].get('totalDistanceMeters', 0) / 1000, 2) if daily_stats[0] and daily_stats[0].get('totalDistanceMeters') else None
            elif isinstance(daily_stats, dict):
                activity_summary["calories_burned"] = daily_stats.get('totalKilocalories')
                activity_summary["distance_km"] = round(daily_stats.get('totalDistanceMeters', 0) / 1000, 2) if daily_stats.get('totalDistanceMeters') else None
        
        return {
            "date": date,
            "activity_summary": activity_summary,
            "raw_data": {
                "steps": steps_data,
                "floors": floors_data,
                "intensity": intensity_data,
                "daily_stats": daily_stats
            }
        }

    @handle_api_errors
    @validate_required_params("race_distance", "race_time")
    async def _calculate_training_paces(self, args: Dict[str, Any]) -> Dict[str, Any]:
        race_distance = args["race_distance"]
        race_time = args["race_time"]
        
        # Parse time using utility function
        try:
            total_seconds = parse_time(race_time)
        except ValueError as e:
            return {"error": str(e)}
        
        distance_meters = DISTANCE_METERS
        
        if race_distance not in distance_meters:
            raise ValueError(f"Unsupported race distance: {race_distance}")
        
        pace_per_km = total_seconds / (distance_meters[race_distance] / 1000)
        
        # Simplified training pace calculations based on race pace
        training_paces = {
            "easy_pace": pace_per_km * 1.2,  # 20% slower
            "marathon_pace": pace_per_km * 1.05,  # 5% slower
            "threshold_pace": pace_per_km * 0.95,  # 5% faster
            "interval_pace": pace_per_km * 0.90,  # 10% faster
            "repetition_pace": pace_per_km * 0.85,  # 15% faster
        }
        
        # Convert back to MM:SS format
        formatted_paces = {}
        for pace_type, pace_seconds in training_paces.items():
            formatted_paces[pace_type] = format_pace(pace_seconds)
        
        return {
            "race_performance": {
                "distance": race_distance,
                "time": race_time,
                "pace_per_km": format_pace(pace_per_km)
            },
            "training_paces": formatted_paces
        }

    @handle_api_errors
    @validate_required_params("activity_id")
    async def _get_advanced_running_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        activity_id = args["activity_id"]
        
        # Get detailed activity data
        activity_details = await asyncio.to_thread(
            self.garmin_client.get_activity_details, activity_id
        )
        
        # Extract advanced running metrics from activity details
        advanced_metrics = {}
        
        # Look for metrics in the detailed data
        if activity_details:
            # Common locations for running dynamics
            summary_dto = activity_details.get('summaryDTO', {})
            metrics_dto = activity_details.get('metricDescriptors', [])
            
            # Extract from summaryDTO
            if summary_dto:
                if 'avgStrideLength' in summary_dto:
                    advanced_metrics['stride_length_m'] = summary_dto['avgStrideLength'] / 100  # Convert cm to m
                if 'avgVerticalRatio' in summary_dto:
                    advanced_metrics['vertical_ratio_percent'] = summary_dto['avgVerticalRatio']
                if 'avgVerticalOscillation' in summary_dto:
                    advanced_metrics['vertical_amplitude_cm'] = summary_dto['avgVerticalOscillation']
                if 'avgGroundContactTime' in summary_dto:
                    advanced_metrics['ground_contact_time_ms'] = summary_dto['avgGroundContactTime']
                if 'avgCadence' in summary_dto:
                    advanced_metrics['cadence_spm'] = summary_dto['avgCadence'] * 2  # Convert to steps per minute
                if 'avgGroundContactBalance' in summary_dto:
                    advanced_metrics['ground_contact_balance_percent'] = summary_dto['avgGroundContactBalance']
            
            # Try to find in other possible locations
            activity_detail_metrics = activity_details.get('activityDetailMetrics', [])
            for metric in activity_detail_metrics:
                metric_key = metric.get('metricKey', '')
                if metric_key == 'directRunCadence':
                    advanced_metrics['cadence_spm'] = metric.get('metricAverage', 0) * 2
                elif metric_key == 'directAvgStrideLength':
                    advanced_metrics['stride_length_m'] = metric.get('metricAverage', 0) / 100
        
        return {
            "activity_id": activity_id,
            "advanced_running_metrics": advanced_metrics,
            "note": "Advanced metrics availability depends on device and activity type",
            "raw_details": activity_details if not advanced_metrics else None
        }

    @handle_api_errors
    @validate_required_params("activity_id")
    async def _analyze_heart_rate_zones(self, args: Dict[str, Any]) -> Dict[str, Any]:
        activity_id = args["activity_id"]
        
        # Get heart rate zones for the activity
        try:
            hr_time_in_zones = await asyncio.to_thread(
                self.garmin_client.get_activity_hr_in_timezones, activity_id
            )
        except Exception as e:
            hr_time_in_zones = None
        
        # Get user's heart rate zones configuration
        try:
            hr_zones_config = await asyncio.to_thread(self.garmin_client.get_heart_rate_zones)
        except:
            hr_zones_config = None
        
        # Process zone distribution if available
        zone_analysis = {}
        if hr_time_in_zones and isinstance(hr_time_in_zones, list):
            total_time = 0
            for zone in hr_time_in_zones:
                zone_time = zone.get('secsInZone', 0)
                total_time += zone_time
            
            for i, zone in enumerate(hr_time_in_zones):
                zone_time = zone.get('secsInZone', 0)
                zone_name = zone.get('zoneName', f'Zone {i+1}')
                percentage = (zone_time / total_time * 100) if total_time > 0 else 0
                
                zone_analysis[zone_name] = {
                    "time_seconds": zone_time,
                    "time_minutes": round(zone_time / 60, 1),
                    "percentage": round(percentage, 1),
                    "min_hr": zone.get('startValue'),
                    "max_hr": zone.get('endValue')
                }
        
        return {
            "activity_id": activity_id,
            "heart_rate_zones_config": hr_zones_config,
            "zone_distribution": zone_analysis,
            "time_in_zones_data": hr_time_in_zones,
            "note": "Zone analysis based on activity heart rate data"
        }

    @handle_api_errors
    @validate_required_params("race_date", "race_distance", "target_time")
    async def _set_race_goal(self, args: Dict[str, Any]) -> Dict[str, Any]:
        race_distance = args["race_distance"]
        target_time = args["target_time"]
        race_date = args["race_date"]
        
        # Calculate target pace
        time_parts = target_time.split(":")
        total_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        
        distance_meters = {
            "5K": 5000,
            "10K": 10000,
            "half_marathon": 21097,
            "marathon": 42195
        }
        
        target_pace_per_km = total_seconds / (distance_meters[race_distance] / 1000)
        target_pace_formatted = format_pace(target_pace_per_km)
        
        # Calculate days until race
        race_date_obj = datetime.strptime(race_date, "%Y-%m-%d")
        days_until_race = (race_date_obj - datetime.now()).days
        
        return {
            "race_goal": {
                "distance": race_distance,
                "target_time": target_time,
                "target_pace_per_km": target_pace_formatted,
                "race_date": race_date,
                "days_until_race": days_until_race
            },
            "training_recommendation": {
                "phase": "build" if days_until_race > 12 else "taper" if days_until_race > 0 else "recovery",
                "note": "Training phase based on time remaining until race"
            }
        }

    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _analyze_training_load(self, args: Dict[str, Any]) -> Dict[str, Any]:
        weeks_back = args.get("weeks_back", 4)
        
        # Get activities for the specified period
        start_date = (datetime.now() - timedelta(weeks=weeks_back)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        activities = await asyncio.to_thread(
            self.garmin_client.get_activities_by_date, start_date, end_date
        )
        
        # Filter running activities
        running_activities = filter_running_activities(activities)
        
        # Calculate training load metrics
        total_distance = sum(activity.get("distance", 0) for activity in running_activities)
        total_time = sum(activity.get("duration", 0) for activity in running_activities)
        activity_count = len(running_activities)
        
        # Weekly breakdown
        weekly_stats = []
        for week in range(weeks_back):
            week_start = datetime.now() - timedelta(weeks=week+1)
            week_end = datetime.now() - timedelta(weeks=week)
            
            week_activities = [
                activity for activity in running_activities
                if week_start <= datetime.strptime(activity.get("startTimeLocal", "")[:10], "%Y-%m-%d") < week_end
            ]
            
            weekly_stats.append({
                "week": f"Week {weeks_back - week}",
                "distance_km": sum(activity.get("distance", 0) for activity in week_activities) / 1000,
                "activity_count": len(week_activities),
                "avg_pace": "calculated_from_activities"  # Would calculate actual average
            })
        
        return {
            "analysis_period": f"{weeks_back} weeks",
            "total_distance_km": total_distance / 1000,
            "total_time_hours": total_time / 3600,
            "activity_count": activity_count,
            "weekly_breakdown": weekly_stats,
            "injury_risk_indicators": {
                "sudden_mileage_increase": False,  # Would calculate actual risk
                "high_intensity_frequency": "normal",
                "recovery_adequacy": "adequate"
            }
        }

    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_running_trends(self, args: Dict[str, Any]) -> Dict[str, Any]:
        months_back = args.get("months_back", 6)
        
        # Calculate the actual start date based on calendar months
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # Calculate start month/year
        start_month = current_month - months_back
        start_year = current_year
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        
        start_date = f"{start_year}-{start_month:02d}-01"
        end_date = now.strftime("%Y-%m-%d")
        
        activities = await asyncio.to_thread(
            self.garmin_client.get_activities_by_date, start_date, end_date
        )
        
        # Filter running activities
        running_activities = filter_running_activities(activities)
        
        # Calculate monthly trends using actual calendar months
        monthly_trends = []
        for i in range(months_back):
            # Calculate the target month and year
            target_month = current_month - i
            target_year = current_year
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Get the first and last day of the month
            month_start = datetime(target_year, target_month, 1)
            month_end = datetime(target_year, target_month, monthrange(target_year, target_month)[1], 23, 59, 59)
            
            month_activities = [
                activity for activity in running_activities
                if month_start <= datetime.strptime(activity.get("startTimeLocal", "")[:10], "%Y-%m-%d") <= month_end
            ]
            
            if month_activities:
                avg_distance = sum(activity.get("distance", 0) for activity in month_activities) / len(month_activities) / 1000
                avg_pace = sum(activity.get("avgSpeed", 0) for activity in month_activities) / len(month_activities)
            else:
                avg_distance = 0
                avg_pace = 0
            
            monthly_trends.append({
                "month": f"{target_year}-{target_month:02d}",
                "activity_count": len(month_activities),
                "avg_distance_km": round(avg_distance, 2),
                "avg_pace_mps": round(avg_pace, 2),
                "total_distance_km": round(sum(activity.get("distance", 0) for activity in month_activities) / 1000, 2)
            })
        
        # Calculate overall trends
        if len(monthly_trends) >= 2:
            recent_avg = sum(trend["total_distance_km"] for trend in monthly_trends[:2]) / 2
            earlier_avg = sum(trend["total_distance_km"] for trend in monthly_trends[-2:]) / 2
            distance_trend = "increasing" if recent_avg > earlier_avg else "decreasing"
        else:
            distance_trend = "insufficient_data"
        
        return {
            "analysis_period": f"{months_back} months",
            "monthly_trends": monthly_trends,
            "overall_trends": {
                "distance_trend": distance_trend,
                "consistency": "regular" if len(running_activities) > months_back * 4 else "irregular"
            }
        }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_lactate_threshold(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        try:
            # Get training status which might include lactate threshold
            training_status = await asyncio.to_thread(self.garmin_client.get_training_status, date)
            
            # Look for lactate threshold data
            lactate_threshold = {}
            if training_status:
                # Extract lactate threshold if available
                if 'lactateThresholdBpm' in training_status:
                    lactate_threshold['heart_rate_bpm'] = training_status['lactateThresholdBpm']
                if 'lactateThresholdSpeed' in training_status:
                    # Convert m/s to pace per km
                    speed_mps = training_status['lactateThresholdSpeed']
                    if speed_mps > 0:
                        pace_seconds = 1000 / speed_mps
                        lactate_threshold['pace_per_km'] = format_pace(pace_seconds)
                        lactate_threshold['speed_kmh'] = round(speed_mps * 3.6, 2)
            
            # Try to get from max metrics as well
            max_metrics = await asyncio.to_thread(self.garmin_client.get_max_metrics, date)
            if max_metrics and isinstance(max_metrics, list):
                for metric in max_metrics:
                    if 'generic' in metric:
                        if 'lactateThresholdBpm' in metric['generic']:
                            lactate_threshold['heart_rate_bpm'] = metric['generic']['lactateThresholdBpm']
                        if 'lactateThresholdSpeed' in metric['generic']:
                            speed_mps = metric['generic']['lactateThresholdSpeed']
                            if speed_mps > 0:
                                pace_seconds = 1000 / speed_mps
                                lactate_threshold['pace_per_km'] = format_pace(pace_seconds)
                                lactate_threshold['speed_kmh'] = round(speed_mps * 3.6, 2)
            
            return {
                "date": date,
                "lactate_threshold": lactate_threshold if lactate_threshold else {
                    "note": "No lactate threshold data found. This requires a compatible Garmin device and sufficient running data."
                },
                "raw_training_status": training_status,
                "raw_max_metrics": max_metrics
            }
        except Exception as e:
            logger.error(f"Failed to get lactate threshold data: {e}")
            return {
                "date": date,
                "error": f"Failed to get lactate threshold data: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_race_predictions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get race predictions from Garmin
            predictions = await asyncio.to_thread(self.garmin_client.get_race_predictions)
            
            # Format predictions for common distances
            formatted_predictions = {}
            if predictions:
                # Map common race distances
                distance_mapping = {
                    5000: "5K",
                    10000: "10K",
                    21097.5: "half_marathon",
                    42195: "marathon"
                }
                
                for prediction in predictions:
                    if isinstance(prediction, dict):
                        distance = prediction.get('distance')
                        if distance in distance_mapping:
                            time_seconds = prediction.get('time')
                            if time_seconds:
                                time_str = format_time(time_seconds)
                                
                                formatted_predictions[distance_mapping[distance]] = {
                                    "predicted_time": time_str,
                                    "predicted_seconds": time_seconds,
                                    "race_readiness_level": prediction.get('raceReadinessLevel'),
                                    "race_readiness_state": prediction.get('raceReadinessState')
                                }
            
            # Get current VO2 Max for context
            vo2_max = None
            try:
                max_metrics = await asyncio.to_thread(self.garmin_client.get_max_metrics, datetime.now().strftime("%Y-%m-%d"))
                if isinstance(max_metrics, list) and len(max_metrics) > 0:
                    for metric in max_metrics:
                        if 'generic' in metric and 'maxMet' in metric['generic']:
                            vo2_max = metric['generic']['maxMet']
                            break
            except:
                pass
            
            return {
                "race_predictions": formatted_predictions if formatted_predictions else {
                    "note": "No race predictions available. This requires recent running activities and a compatible Garmin device."
                },
                "current_vo2_max": vo2_max,
                "raw_predictions": predictions
            }
        except Exception as e:
            logger.error(f"Failed to get race predictions: {e}")
            return {
                "error": f"Failed to get race predictions: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_training_readiness(self, args: Dict[str, Any]) -> Dict[str, Any]:
        date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        try:
            # Get training readiness
            readiness = await asyncio.to_thread(self.garmin_client.get_training_readiness, date)
            
            # Process readiness data
            readiness_summary = {}
            if readiness:
                # Handle both list and dict responses
                if isinstance(readiness, list) and len(readiness) > 0:
                    # Use the most recent readiness data
                    latest_readiness = readiness[-1] if readiness else {}
                    readiness_summary = {
                        "score": latest_readiness.get('score'),
                        "level": latest_readiness.get('level'),
                        "message": latest_readiness.get('message'),
                        "recovery_level": latest_readiness.get('recoveryLevel'),
                        "training_load_balance": latest_readiness.get('trainingLoadBalance'),
                        "sleep_quality": latest_readiness.get('sleepQuality'),
                        "hrv_status": latest_readiness.get('hrvStatus')
                    }
                elif isinstance(readiness, dict):
                    readiness_summary = {
                        "score": readiness.get('score'),
                        "level": readiness.get('level'),
                        "message": readiness.get('message'),
                        "recovery_level": readiness.get('recoveryLevel'),
                        "training_load_balance": readiness.get('trainingLoadBalance'),
                        "sleep_quality": readiness.get('sleepQuality'),
                        "hrv_status": readiness.get('hrvStatus')
                    }
            
            # Get recovery time for additional context
            recovery_time = None
            try:
                training_status = await asyncio.to_thread(self.garmin_client.get_training_status, date)
                if training_status:
                    recovery_time = training_status.get('recoveryTime')
            except:
                pass
            
            return {
                "date": date,
                "training_readiness": readiness_summary if readiness_summary else {
                    "note": "No training readiness data available. This feature requires a compatible Garmin device."
                },
                "recovery_time_hours": recovery_time,
                "raw_readiness_data": readiness
            }
        except Exception as e:
            logger.error(f"Failed to get training readiness: {e}")
            return {
                "date": date,
                "error": f"Failed to get training readiness: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_recovery_time(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get recovery time from training status
            date = args.get("date", datetime.now().strftime("%Y-%m-%d"))
            training_status = await asyncio.to_thread(self.garmin_client.get_training_status, date)
            
            recovery_info = {}
            if training_status:
                recovery_hours = training_status.get('recoveryTime', 0)
                recovery_info = {
                    "recovery_time_hours": recovery_hours,
                    "recovery_time_formatted": f"{int(recovery_hours)} hours",
                    "fully_recovered_at": (datetime.now() + timedelta(hours=recovery_hours)).strftime("%Y-%m-%d %H:%M") if recovery_hours else "Already recovered"
                }
            
            # Get last activity for context
            last_activity = None
            try:
                last_activity_data = await asyncio.to_thread(self.garmin_client.get_last_activity)
                if last_activity_data:
                    last_activity = {
                        "activity_name": last_activity_data.get('activityName'),
                        "activity_type": last_activity_data.get('activityType', {}).get('typeKey'),
                        "start_time": last_activity_data.get('startTimeLocal'),
                        "training_effect": {
                            "aerobic": last_activity_data.get('aerobicTrainingEffect'),
                            "anaerobic": last_activity_data.get('anaerobicTrainingEffect')
                        }
                    }
            except:
                pass
            
            return {
                "recovery_info": recovery_info if recovery_info else {
                    "note": "No recovery time data available."
                },
                "last_activity": last_activity,
                "training_status": {
                    "status": training_status.get('trainingStatusType') if training_status else None,
                    "fitness_level": training_status.get('fitnessLevel') if training_status else None
                }
            }
        except Exception as e:
            logger.error(f"Failed to get recovery time: {e}")
            return {
                "error": f"Failed to get recovery time: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_training_load_balance(self, args: Dict[str, Any]) -> Dict[str, Any]:
        weeks_back = args.get("weeks_back", 6)
        
        try:
            # Get activities for the analysis period
            start_date = (datetime.now() - timedelta(weeks=weeks_back)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            activities = await asyncio.to_thread(
                self.garmin_client.get_activities_by_date, start_date, end_date
            )
            
            # Filter running activities
            running_activities = filter_running_activities(activities)
            
            # Calculate daily training loads
            daily_loads = {}
            for activity in running_activities:
                date = activity.get("startTimeLocal", "")[:10]
                
                # Calculate training load (simplified: duration * intensity)
                duration_hours = activity.get("duration", 0) / 3600
                avg_hr = activity.get("averageHR", 0)
                max_hr = activity.get("maxHR", DEFAULT_MAX_HR)  # Default max HR
                
                # Intensity factor based on heart rate
                intensity = (avg_hr / max_hr) if max_hr > 0 and avg_hr > 0 else 0.7
                
                # Training impulse (TRIMP) calculation
                trimp = duration_hours * 60 * intensity * 100  # Simplified TRIMP
                
                if date in daily_loads:
                    daily_loads[date] += trimp
                else:
                    daily_loads[date] = trimp
            
            # Calculate ATL (Acute Training Load - 7 days) and CTL (Chronic Training Load - 28 days)
            today = datetime.now()
            atl_sum = 0
            atl_days = 0
            ctl_sum = 0
            ctl_days = 0
            
            for i in range(42):  # Look back 42 days to ensure we have enough data
                date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                load = daily_loads.get(date, 0)
                
                if i < 7:  # Last 7 days for ATL
                    atl_sum += load
                    atl_days += 1
                
                if i < 28:  # Last 28 days for CTL
                    ctl_sum += load
                    ctl_days += 1
            
            atl = atl_sum / atl_days if atl_days > 0 else 0
            ctl = ctl_sum / ctl_days if ctl_days > 0 else 0
            
            # Calculate training stress balance
            tsb = ctl - atl  # Positive means fresh, negative means fatigued
            
            # ATL:CTL ratio for injury risk
            ratio = atl / ctl if ctl > 0 else 0
            
            # Determine training load status
            if ratio < 0.8:
                load_status = "Low - Consider increasing training"
            elif ratio < 1.0:
                load_status = "Optimal - Good balance"
            elif ratio < 1.3:
                load_status = "High - Monitor fatigue"
            elif ratio < 1.5:
                load_status = "Very High - Injury risk elevated"
            else:
                load_status = "Dangerous - High injury risk"
            
            # Weekly load progression
            weekly_loads = []
            for week in range(weeks_back):
                week_start = today - timedelta(weeks=week+1)
                week_end = today - timedelta(weeks=week)
                week_load = 0
                
                for day in range(7):
                    date = (week_start + timedelta(days=day)).strftime("%Y-%m-%d")
                    week_load += daily_loads.get(date, 0)
                
                weekly_loads.append({
                    "week": f"Week -{week+1}",
                    "total_load": round(week_load, 1),
                    "daily_average": round(week_load / 7, 1)
                })
            
            return {
                "training_load_metrics": {
                    "acute_load_atl": round(atl, 1),
                    "chronic_load_ctl": round(ctl, 1),
                    "training_stress_balance": round(tsb, 1),
                    "atl_ctl_ratio": round(ratio, 2),
                    "load_status": load_status
                },
                "weekly_progression": weekly_loads,
                "recommendations": {
                    "current_state": "Fresh and ready" if tsb > 0 else "Fatigued",
                    "injury_risk": "Low" if ratio < 1.0 else "Moderate" if ratio < 1.3 else "High",
                    "suggested_action": "Maintain current load" if 0.8 <= ratio <= 1.0 else "Adjust training load"
                },
                "analysis_period": f"{weeks_back} weeks",
                "activity_count": len(running_activities)
            }
        except Exception as e:
            logger.error(f"Failed to get training load balance: {e}")
            return {
                "error": f"Failed to get training load balance: {str(e)}"
            }
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _get_training_effect(self, args: Dict[str, Any]) -> Dict[str, Any]:
        days_back = args.get("days_back", 7)
        
        try:
            # Get recent activities
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            activities = await asyncio.to_thread(
                self.garmin_client.get_activities_by_date, start_date, end_date
            )
            
            # Filter running activities and extract training effects
            training_effects = []
            running_activities = filter_running_activities(activities)
            for activity in running_activities:
                    aerobic = activity.get("aerobicTrainingEffect")
                    anaerobic = activity.get("anaerobicTrainingEffect")
                    
                    if aerobic is not None or anaerobic is not None:
                        training_effects.append({
                            "date": activity.get("startTimeLocal", "")[:10],
                            "activity_name": activity.get("activityName"),
                            "aerobic_effect": aerobic,
                            "anaerobic_effect": anaerobic,
                            "duration_minutes": round(activity.get("duration", 0) / 60, 1),
                            "distance_km": round(activity.get("distance", 0) / 1000, 2)
                        })
            
            # Calculate summary statistics
            if training_effects:
                avg_aerobic = sum(e["aerobic_effect"] for e in training_effects if e["aerobic_effect"] is not None) / len([e for e in training_effects if e["aerobic_effect"] is not None])
                avg_anaerobic = sum(e["anaerobic_effect"] for e in training_effects if e["anaerobic_effect"] is not None) / len([e for e in training_effects if e["anaerobic_effect"] is not None])
                
                # Determine training focus
                if avg_aerobic > avg_anaerobic * 1.5:
                    focus = "Aerobic base building"
                elif avg_anaerobic > avg_aerobic * 1.5:
                    focus = "Speed and power development"
                else:
                    focus = "Balanced aerobic and anaerobic"
                
                # Training effect interpretation
                def interpret_effect(value):
                    if value < 0.5:
                        return "No benefit"
                    elif value < 1.0:
                        return "Minor benefit"
                    elif value < 2.0:
                        return "Maintaining fitness"
                    elif value < 3.0:
                        return "Improving fitness"
                    elif value < 4.0:
                        return "Highly improving"
                    else:
                        return "Overreaching"
                
                summary = {
                    "average_aerobic_effect": round(avg_aerobic, 1),
                    "average_anaerobic_effect": round(avg_anaerobic, 1),
                    "training_focus": focus,
                    "aerobic_benefit": interpret_effect(avg_aerobic),
                    "anaerobic_benefit": interpret_effect(avg_anaerobic),
                    "total_activities": len(training_effects)
                }
            else:
                summary = {
                    "note": "No activities with training effect data found in the specified period."
                }
            
            return {
                "period": f"Last {days_back} days",
                "summary": summary,
                "activities": training_effects,
                "recommendations": {
                    "aerobic": "Increase easy runs and long runs" if summary.get("average_aerobic_effect", 0) < 2.0 else "Maintain current aerobic training",
                    "anaerobic": "Add intervals or tempo runs" if summary.get("average_anaerobic_effect", 0) < 2.0 else "Maintain current intensity work",
                    "recovery": "Consider recovery day" if summary.get("average_aerobic_effect", 0) > 3.5 or summary.get("average_anaerobic_effect", 0) > 3.5 else "Training load is appropriate"
                }
            }
        except Exception as e:
            logger.error(f"Failed to get training effect data: {e}")
            return {
                "error": f"Failed to get training effect data: {str(e)}"
            }
    
    @handle_api_errors
    @validate_required_params("race_distance", "race_time")
    async def _calculate_vdot_zones(self, args: Dict[str, Any]) -> Dict[str, Any]:
        race_distance = args["race_distance"]
        race_time = args["race_time"]
        
        # Parse race time using utility function
        try:
            total_seconds = parse_time(race_time)
        except ValueError as e:
            return {"error": str(e)}
        
        # Use constant for distance meters
        distance_meters = DISTANCE_METERS
        
        if race_distance not in distance_meters:
            raise ValueError(f"Unsupported race distance: {race_distance}")
        
        # Calculate VDOT using utility function
        vdot = calculate_vdot_from_time(distance_meters[race_distance], total_seconds)
        
        # Calculate training paces using utility function
        formatted_zones = calculate_training_paces_from_vdot(vdot)
        
        # Calculate equivalent race times based on VDOT
        # Using standard VDOT tables for common distances
        equivalent_times = {
            "5K": format_time(1080 * (50 / vdot)) if vdot >= 30 else "N/A",
            "10K": format_time(2250 * (50 / vdot)) if vdot >= 30 else "N/A",
            "half_marathon": format_time(4980 * (50 / vdot)) if vdot >= 30 else "N/A",
            "marathon": format_time(10440 * (50 / vdot)) if vdot >= 30 else "N/A"
        }
        
        return {
            "vdot": vdot,
            "race_input": {
                "distance": race_distance,
                "time": race_time,
                "pace_per_km": format_pace(total_seconds / (distance_meters[race_distance] / 1000))
            },
            "training_zones": formatted_zones,
            "equivalent_race_times": equivalent_times,
            "training_recommendations": {
                "easy_runs": "60-70% of weekly mileage at easy pace",
                "quality_workouts": "2-3 per week at threshold/interval pace",
                "long_runs": "20-25% of weekly mileage at easy to marathon pace"
            }
        }
    
    
    @handle_api_errors
    @cached(cache_duration_hours=1.0)
    async def _analyze_threshold_zones(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get lactate threshold data
            threshold_data = await self._get_lactate_threshold({})
            
            threshold_zones = {}
            if threshold_data.get("lactate_threshold"):
                lt_pace = threshold_data["lactate_threshold"].get("pace_per_km")
                lt_hr = threshold_data["lactate_threshold"].get("heart_rate_bpm")
                
                if lt_pace:
                    # Parse threshold pace
                    pace_parts = lt_pace.split(":")
                    lt_seconds = int(pace_parts[0]) * 60 + int(pace_parts[1])
                    
                    # Calculate double threshold zones (Norwegian method)
                    threshold_zones = {
                        "threshold_1": {
                            "description": "Lower threshold - Marathon to Half Marathon pace",
                            "pace_range": f"{format_pace(lt_seconds * 1.08)} - {format_pace(lt_seconds * 1.04)}",
                            "heart_rate": f"{int(lt_hr * 0.92)}-{int(lt_hr * 0.95)} bpm" if lt_hr else "88-92% of threshold HR",
                            "duration": "15-30 minutes continuous or 3x10-15min intervals",
                            "purpose": "Improve aerobic capacity and fatigue resistance"
                        },
                        "threshold_2": {
                            "description": "Upper threshold - 10K to 15K pace",
                            "pace_range": f"{format_pace(lt_seconds * 1.02)} - {format_pace(lt_seconds * 0.98)}",
                            "heart_rate": f"{int(lt_hr * 0.98)}-{int(lt_hr * 1.02)} bpm" if lt_hr else "98-102% of threshold HR",
                            "duration": "8-15 minutes intervals with short recovery",
                            "purpose": "Improve lactate buffering and threshold pace"
                        },
                        "threshold_intervals": {
                            "description": "Classic threshold intervals",
                            "pace_range": f"{format_pace(lt_seconds * 1.01)} - {format_pace(lt_seconds * 0.99)}",
                            "heart_rate": f"{int(lt_hr * 0.99)}-{int(lt_hr * 1.01)} bpm" if lt_hr else "At threshold HR",
                            "duration": "5-8 x 5-8 minutes with 60-90s recovery",
                            "purpose": "Precisely target lactate threshold improvement"
                        }
                    }
                    
                    # Weekly workout suggestions
                    workout_plan = {
                        "tuesday": "Threshold 1: 2x15min at lower threshold with 3min recovery",
                        "thursday": "Threshold 2: 5x8min at upper threshold with 90s recovery",
                        "saturday": "Long run with threshold segments: Include 3x10min at Threshold 1",
                        "frequency": "2-3 threshold sessions per week during build phase"
                    }
                else:
                    threshold_zones = {
                        "note": "No lactate threshold pace data available. Run a recent time trial or race for accurate zones."
                    }
                    workout_plan = {}
            else:
                threshold_zones = {
                    "note": "Lactate threshold data not available. This requires compatible Garmin device and recent threshold test."
                }
                workout_plan = {}
            
            return {
                "threshold_zones": threshold_zones,
                "weekly_workout_plan": workout_plan,
                "norwegian_method_principles": {
                    "volume": "High volume at threshold intensities",
                    "frequency": "Multiple threshold sessions per week",
                    "recovery": "Easy days truly easy (65-75% max HR)",
                    "progression": "Gradually increase interval duration before pace"
                },
                "threshold_data": threshold_data.get("lactate_threshold", {})
            }
        except Exception as e:
            logger.error(f"Failed to analyze threshold zones: {e}")
            return {
                "error": f"Failed to analyze threshold zones: {str(e)}"
            }
    
    @handle_api_errors
    async def _suggest_daily_workout(self, args: Dict[str, Any]) -> Dict[str, Any]:
        training_phase = args.get("training_phase", "build")
        
        try:
            # Get current training status and readiness
            readiness_data = await self._get_training_readiness({})
            recovery_data = await self._get_recovery_time({})
            load_balance = await self._get_training_load_balance({"weeks_back": 2})
            
            # Extract key metrics
            readiness_score = readiness_data.get("training_readiness", {}).get("score", 50)
            recovery_hours = recovery_data.get("recovery_info", {}).get("recovery_time_hours", 0)
            atl_ctl_ratio = load_balance.get("training_load_metrics", {}).get("atl_ctl_ratio", 1.0)
            
            # Determine workout based on multiple factors
            if recovery_hours > 24:
                workout_type = "recovery"
                intensity = "easy"
            elif atl_ctl_ratio > 1.3:
                workout_type = "easy"
                intensity = "low"
            elif readiness_score < 25:
                workout_type = "rest"
                intensity = "none"
            else:
                # Base workout on training phase
                phase_workouts = {
                    "base": ["easy", "easy", "tempo", "easy", "long"],
                    "build": ["easy", "intervals", "easy", "tempo", "long"],
                    "peak": ["easy", "intervals", "tempo", "easy", "race_pace"],
                    "taper": ["easy", "short_intervals", "easy", "race_pace", "easy"],
                    "recovery": ["easy", "easy", "easy", "easy", "easy_long"]
                }
                
                # Get day of week (0 = Monday)
                day_of_week = datetime.now().weekday()
                workout_options = phase_workouts.get(training_phase, phase_workouts["build"])
                workout_type = workout_options[day_of_week % len(workout_options)]
                
                # Adjust intensity based on readiness
                if readiness_score > 75:
                    intensity = "high"
                elif readiness_score > 50:
                    intensity = "moderate"
                else:
                    intensity = "low"
            
            # Get specific workout details
            workout_details = self._get_workout_details(workout_type, intensity)
            
            # Get recent training for context
            recent_effect = await self._get_training_effect({"days_back": 3})
            recent_aerobic = recent_effect.get("summary", {}).get("average_aerobic_effect", 0)
            recent_anaerobic = recent_effect.get("summary", {}).get("average_anaerobic_effect", 0)
            
            # Adjust recommendations based on recent training
            if recent_aerobic < 2.0:
                workout_details["note"] = "Focus on aerobic development"
            elif recent_anaerobic < 1.5 and workout_type in ["intervals", "tempo"]:
                workout_details["note"] = "Good day for quality work"
            
            return {
                "recommended_workout": workout_details,
                "current_status": {
                    "training_phase": training_phase,
                    "readiness_score": readiness_score,
                    "recovery_hours_remaining": recovery_hours,
                    "training_load_ratio": round(atl_ctl_ratio, 2)
                },
                "rationale": f"Based on your {training_phase} phase and current readiness",
                "alternative_options": self._get_alternative_workouts(workout_type),
                "tomorrow_preview": "Check training readiness tomorrow morning for updated recommendation"
            }
        except Exception as e:
            logger.error(f"Failed to suggest workout: {e}")
            # Provide fallback suggestion
            return {
                "recommended_workout": {
                    "type": "easy",
                    "description": "Easy recovery run",
                    "duration": "30-45 minutes",
                    "intensity": "Conversational pace",
                    "notes": "Listen to your body"
                },
                "error": f"Could not access all metrics: {str(e)}",
                "fallback": True
            }
    
    def _get_workout_details(self, workout_type: str, intensity: str) -> Dict[str, Any]:
        """Get detailed workout prescription"""
        workouts = {
            "easy": {
                "description": "Easy recovery run",
                "duration": "30-60 minutes",
                "pace": "Easy/conversational pace",
                "heart_rate": "Zone 1-2 (65-75% max HR)",
                "notes": "Focus on relaxed form and breathing"
            },
            "tempo": {
                "description": "Threshold tempo run",
                "warmup": "15 minutes easy",
                "main": "20-40 minutes at threshold pace" if intensity == "high" else "15-25 minutes at threshold pace",
                "cooldown": "10 minutes easy",
                "pace": "Comfortably hard - can speak in short sentences",
                "heart_rate": "Zone 3-4 (85-92% max HR)"
            },
            "intervals": {
                "description": "VO2max intervals",
                "warmup": "15 minutes easy + 4x100m strides",
                "main": "6x1000m at 5K pace with 2-3min recovery" if intensity == "high" else "4x1000m at 5K pace with 3min recovery",
                "cooldown": "10 minutes easy",
                "pace": "5K race pace or slightly faster",
                "heart_rate": "Zone 5 (95-100% max HR) during intervals"
            },
            "long": {
                "description": "Long endurance run",
                "duration": "90-150 minutes" if intensity == "high" else "60-90 minutes",
                "pace": "Easy to moderate pace",
                "heart_rate": "Zone 2 (70-80% max HR)",
                "notes": "Consider fueling after 60 minutes"
            },
            "recovery": {
                "description": "Recovery run",
                "duration": "20-40 minutes",
                "pace": "Very easy - slower than normal easy pace",
                "heart_rate": "Zone 1 (60-70% max HR)",
                "notes": "Focus on form and relaxation"
            },
            "rest": {
                "description": "Rest day",
                "activities": "Complete rest or light cross-training",
                "notes": "Recovery is when adaptation occurs"
            }
        }
        
        return workouts.get(workout_type, workouts["easy"])
    
    def _get_alternative_workouts(self, primary_type: str) -> List[str]:
        """Suggest alternative workout options"""
        alternatives = {
            "easy": ["recovery run", "cross-training", "yoga"],
            "tempo": ["progression run", "cruise intervals", "steady state run"],
            "intervals": ["fartlek", "hill repeats", "track workout"],
            "long": ["progressive long run", "easy long run", "marathon pace segments"],
            "recovery": ["pool running", "easy bike", "walk"]
        }
        
        return alternatives.get(primary_type, ["easy run", "cross-training"])
    
    @handle_api_errors
    @validate_required_params("activity_id")
    async def _analyze_workout_quality(self, args: Dict[str, Any]) -> Dict[str, Any]:
        activity_id = args["activity_id"]
        planned_workout = args.get("planned_workout", {})
        
        try:
            # Get activity details
            activity_data = await self._get_activity_summary({"activity_id": activity_id})
            detailed_data = await self._get_activity_details({"activity_id": activity_id})
            hr_zones = await self._analyze_heart_rate_zones({"activity_id": activity_id})
            
            # Extract actual workout metrics
            actual_distance = activity_data.get("distance_km", 0)
            actual_duration = activity_data.get("duration_seconds", 0)
            actual_pace = activity_data.get("average_pace_per_km")
            
            # Parse actual pace
            actual_pace_seconds = None
            if actual_pace:
                pace_parts = actual_pace.split(":")
                if len(pace_parts) == 2:
                    actual_pace_seconds = int(pace_parts[0]) * 60 + int(pace_parts[1])
            
            # Analyze execution quality
            execution_analysis = {}
            
            # Compare distance if planned
            if planned_workout.get("target_distance"):
                target_distance = planned_workout["target_distance"]
                distance_diff = actual_distance - target_distance
                distance_accuracy = (1 - abs(distance_diff) / target_distance) * 100
                
                execution_analysis["distance"] = {
                    "planned": f"{target_distance} km",
                    "actual": f"{actual_distance} km",
                    "difference": f"{distance_diff:+.2f} km",
                    "accuracy": f"{distance_accuracy:.1f}%",
                    "assessment": "Good" if distance_accuracy > 95 else "Acceptable" if distance_accuracy > 90 else "Off target"
                }
            
            # Compare pace if planned
            if planned_workout.get("target_pace") and actual_pace_seconds:
                target_pace = planned_workout["target_pace"]
                target_parts = target_pace.split(":")
                target_pace_seconds = int(target_parts[0]) * 60 + int(target_parts[1])
                
                pace_diff = actual_pace_seconds - target_pace_seconds
                pace_accuracy = (1 - abs(pace_diff) / target_pace_seconds) * 100
                
                execution_analysis["pace"] = {
                    "planned": target_pace,
                    "actual": actual_pace,
                    "difference": f"{pace_diff:+d} seconds/km",
                    "accuracy": f"{pace_accuracy:.1f}%",
                    "assessment": "Excellent" if pace_accuracy > 97 else "Good" if pace_accuracy > 94 else "Needs work"
                }
            
            # Analyze heart rate distribution
            zone_distribution = hr_zones.get("zone_distribution", {})
            workout_type = planned_workout.get("type", "unknown")
            
            # Expected zone distribution by workout type
            expected_zones = {
                "easy": {"Zone 1": 20, "Zone 2": 70, "Zone 3": 10},
                "tempo": {"Zone 3": 60, "Zone 4": 30, "Zone 2": 10},
                "interval": {"Zone 5": 40, "Zone 4": 20, "Zone 1": 20, "Zone 2": 20},
                "long": {"Zone 2": 80, "Zone 3": 15, "Zone 1": 5}
            }
            
            if workout_type in expected_zones:
                hr_assessment = self._assess_hr_distribution(zone_distribution, expected_zones[workout_type])
                execution_analysis["heart_rate"] = hr_assessment
            
            # Get splits for pacing analysis
            splits_data = detailed_data.get("splits", [])
            if splits_data:
                pacing_analysis = self._analyze_pacing(splits_data)
                execution_analysis["pacing"] = pacing_analysis
            
            # Overall workout quality score
            quality_score = self._calculate_workout_quality_score(execution_analysis)
            
            # Training effect assessment
            training_effect = {
                "aerobic": activity_data.get("training_effect", {}).get("aerobic"),
                "anaerobic": activity_data.get("training_effect", {}).get("anaerobic")
            }
            
            return {
                "workout_summary": {
                    "activity_name": activity_data.get("activity_name"),
                    "date": activity_data.get("start_time"),
                    "type": workout_type
                },
                "execution_analysis": execution_analysis,
                "quality_score": quality_score,
                "training_effect": training_effect,
                "recommendations": self._get_workout_recommendations(execution_analysis, workout_type),
                "key_takeaways": self._get_workout_takeaways(execution_analysis, quality_score)
            }
        except Exception as e:
            logger.error(f"Failed to analyze workout quality: {e}")
            return {
                "error": f"Failed to analyze workout quality: {str(e)}"
            }
    
    def _assess_hr_distribution(self, actual: Dict, expected: Dict) -> Dict[str, Any]:
        """Assess heart rate zone distribution against expected"""
        assessment = {
            "distribution": actual,
            "expected": expected,
            "zones_analysis": {}
        }
        
        for zone, expected_pct in expected.items():
            actual_pct = actual.get(zone, {}).get("percentage", 0)
            diff = actual_pct - expected_pct
            
            assessment["zones_analysis"][zone] = {
                "expected": f"{expected_pct}%",
                "actual": f"{actual_pct}%",
                "assessment": "On target" if abs(diff) < 10 else "Off target"
            }
        
        return assessment
    
    def _analyze_pacing(self, splits: List[Dict]) -> Dict[str, Any]:
        """Analyze pacing consistency across splits"""
        if not splits:
            return {"note": "No split data available"}
        
        # Extract pace from each split
        split_paces = []
        for split in splits:
            if isinstance(split, dict) and "averageSpeed" in split:
                # Convert m/s to pace per km
                speed_mps = split["averageSpeed"]
                if speed_mps > 0:
                    pace_seconds = 1000 / (speed_mps * 60)
                    split_paces.append(pace_seconds)
        
        if not split_paces:
            return {"note": "Could not extract pace data from splits"}
        
        # Calculate pacing metrics
        avg_pace = sum(split_paces) / len(split_paces)
        pace_std = (sum((p - avg_pace) ** 2 for p in split_paces) / len(split_paces)) ** 0.5
        variation_coefficient = (pace_std / avg_pace) * 100
        
        # Assess pacing
        if variation_coefficient < 3:
            pacing_quality = "Excellent - very consistent"
        elif variation_coefficient < 5:
            pacing_quality = "Good - well controlled"
        elif variation_coefficient < 8:
            pacing_quality = "Fair - some variation"
        else:
            pacing_quality = "Poor - work on pacing control"
        
        return {
            "variation": f"{variation_coefficient:.1f}%",
            "assessment": pacing_quality,
            "splits_analyzed": len(split_paces)
        }
    
    def _calculate_workout_quality_score(self, analysis: Dict) -> Dict[str, Any]:
        """Calculate overall workout quality score"""
        scores = []
        
        # Distance score
        if "distance" in analysis:
            accuracy = float(analysis["distance"]["accuracy"].rstrip("%"))
            scores.append(accuracy)
        
        # Pace score
        if "pace" in analysis:
            accuracy = float(analysis["pace"]["accuracy"].rstrip("%"))
            scores.append(accuracy)
        
        # HR zone score (simplified)
        if "heart_rate" in analysis:
            # Count zones that are on target
            zones_analysis = analysis["heart_rate"].get("zones_analysis", {})
            on_target = sum(1 for z in zones_analysis.values() if z["assessment"] == "On target")
            total_zones = len(zones_analysis)
            if total_zones > 0:
                hr_score = (on_target / total_zones) * 100
                scores.append(hr_score)
        
        # Calculate overall score
        if scores:
            overall_score = sum(scores) / len(scores)
        else:
            overall_score = 0
        
        # Grade the workout
        if overall_score >= 95:
            grade = "A+"
        elif overall_score >= 90:
            grade = "A"
        elif overall_score >= 85:
            grade = "B+"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 75:
            grade = "C+"
        elif overall_score >= 70:
            grade = "C"
        else:
            grade = "D"
        
        return {
            "overall_score": round(overall_score, 1),
            "grade": grade,
            "components": len(scores)
        }
    
    def _get_workout_recommendations(self, analysis: Dict, workout_type: str) -> List[str]:
        """Generate recommendations based on workout analysis"""
        recommendations = []
        
        # Pace recommendations
        if "pace" in analysis:
            if "faster" in analysis["pace"]["difference"]:
                recommendations.append("Consider slowing down to stay in target zone")
            elif "slower" in analysis["pace"]["difference"] and abs(int(analysis["pace"]["difference"].split()[0])) > 10:
                recommendations.append("Work on maintaining target pace - consider shorter intervals")
        
        # Pacing recommendations
        if "pacing" in analysis:
            variation = float(analysis["pacing"]["variation"].rstrip("%"))
            if variation > 5:
                recommendations.append("Focus on even pacing - use shorter feedback intervals")
        
        # HR recommendations
        if "heart_rate" in analysis:
            zones_analysis = analysis["heart_rate"].get("zones_analysis", {})
            if workout_type == "easy" and zones_analysis.get("Zone 3", {}).get("assessment") == "Off target":
                recommendations.append("Keep effort easier to stay in aerobic zones")
        
        if not recommendations:
            recommendations.append("Good workout execution - maintain this consistency")
        
        return recommendations
    
    def _get_workout_takeaways(self, analysis: Dict, quality_score: Dict) -> List[str]:
        """Generate key takeaways from workout"""
        takeaways = []
        
        grade = quality_score.get("grade", "")
        if grade.startswith("A"):
            takeaways.append("Excellent workout execution!")
        elif grade.startswith("B"):
            takeaways.append("Good workout with room for minor improvements")
        else:
            takeaways.append("Focus on workout execution in future sessions")
        
        # Specific takeaways
        if "pace" in analysis and analysis["pace"]["assessment"] == "Excellent":
            takeaways.append("Pace control was on point")
        
        if "pacing" in analysis and "Excellent" in analysis["pacing"]["assessment"]:
            takeaways.append("Very consistent pacing throughout")
        
        return takeaways

    async def run(self):
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="garmin-connect-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    mcp_server = GarminConnectMCP()
    await mcp_server.run()

if __name__ == "__main__":
    asyncio.run(main())

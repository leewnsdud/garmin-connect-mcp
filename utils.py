#!/usr/bin/env python3
"""Utility functions and decorators for Garmin Connect MCP server."""

import asyncio
import functools
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

# Type variable for decorators
F = TypeVar('F', bound=Callable[..., Any])

# Constants
DEFAULT_MAX_HR = 180
RUNNING_ACTIVITY_TYPES = ["running", "track_running", "trail_running", "treadmill_running"]
DISTANCE_TYPE_IDS = {
    3: '5K',
    4: '10K',
    5: 'half_marathon',
    6: 'marathon'
}

# Distance conversions
DISTANCE_METERS = {
    "5K": 5000,
    "10K": 10000,
    "half_marathon": 21097,
    "marathon": 42195
}

# Cache storage
_cache: Dict[str, Dict[str, Any]] = {}

class GarminAPIError(Exception):
    """Custom exception for Garmin API errors."""
    pass

def handle_api_errors(func: F) -> F:
    """Decorator to handle API errors consistently."""
    @functools.wraps(func)
    async def wrapper(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await func(self, args)
        except Exception as e:
            logger.error(f"{func.__name__} failed: {str(e)}")
            return {"error": f"API call failed: {str(e)}"}
    return wrapper

def validate_required_params(*params: str) -> Callable[[F], F]:
    """Decorator to validate required parameters."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, args: Dict[str, Any]) -> Dict[str, Any]:
            missing = [p for p in params if not args.get(p)]
            if missing:
                return {"error": f"Missing required parameters: {', '.join(missing)}"}
            return await func(self, args)
        return wrapper
    return decorator

def with_retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[F], F]:
    """Decorator to retry failed API calls with exponential backoff."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), retrying in {wait_time}s: {str(e)}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {str(e)}")
            raise last_exception
        return wrapper
    return decorator

def cached(cache_duration_hours: float = 1.0) -> Callable[[F], F]:
    """Decorator to cache API responses for specified duration."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, args: Dict[str, Any]) -> Dict[str, Any]:
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(sorted(args.items()))}"
            
            # Check if cached result exists and is still valid
            if cache_key in _cache:
                cached_data = _cache[cache_key]
                if datetime.now() < cached_data['expires_at']:
                    logger.debug(f"Returning cached result for {func.__name__}")
                    return cached_data['data']
            
            # Call the actual function
            result = await func(self, args)
            
            # Cache the result if it's not an error
            if not (isinstance(result, dict) and 'error' in result):
                _cache[cache_key] = {
                    'data': result,
                    'expires_at': datetime.now() + timedelta(hours=cache_duration_hours)
                }
            
            return result
        return wrapper
    return decorator

def filter_running_activities(activities: List[Dict]) -> List[Dict]:
    """Filter activities to only include running types."""
    return [
        activity for activity in activities
        if activity.get("activityType", {}).get("typeKey") in RUNNING_ACTIVITY_TYPES
    ]

def format_time(seconds: Optional[float]) -> str:
    """Format seconds into HH:MM:SS or MM:SS format."""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_pace(seconds_per_km: Optional[float]) -> str:
    """Format pace from seconds per km to MM:SS format."""
    if seconds_per_km is None:
        return "N/A"
    
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}"

def parse_time(time_str: str) -> int:
    """Parse time string (MM:SS or HH:MM:SS) to seconds."""
    time_parts = time_str.split(":")
    
    if len(time_parts) == 2:  # MM:SS format
        return int(time_parts[0]) * 60 + int(time_parts[1])
    elif len(time_parts) == 3:  # HH:MM:SS format
        return int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
    else:
        raise ValueError(f"Invalid time format: {time_str}. Use MM:SS or HH:MM:SS")

def meters_per_second_to_pace(speed_mps: float) -> str:
    """Convert speed in m/s to pace per km."""
    if speed_mps <= 0:
        return "N/A"
    
    seconds_per_km = 1000 / speed_mps
    return format_pace(seconds_per_km)

def calculate_vdot_from_time(distance_meters: int, time_seconds: int) -> float:
    """Calculate VDOT from race distance and time using Jack Daniels' formula."""
    # Convert to minutes
    time_minutes = time_seconds / 60
    
    # Velocity in meters per minute
    velocity = distance_meters / time_minutes
    
    # Simplified VDOT calculation
    # This is an approximation of Jack Daniels' formula
    percent_max = 0.8 + 0.1894393 * pow(2.718281828, -0.012778 * time_minutes) + 0.2989558 * pow(2.718281828, -0.1932605 * time_minutes)
    vo2 = velocity * 0.182258 + velocity * velocity * 0.000104
    vdot = vo2 / percent_max
    
    return round(vdot, 1)

def calculate_training_paces_from_vdot(vdot: float) -> Dict[str, Dict[str, Any]]:
    """Calculate training paces based on VDOT value."""
    # These formulas are based on Jack Daniels' Running Formula
    # Percentages of VDOT for different training paces
    pace_percentages = {
        "easy": (0.59, 0.74),  # 59-74% of VDOT
        "marathon": 0.84,      # 84% of VDOT
        "threshold": 0.88,     # 88% of VDOT
        "interval": 0.98,      # 98% of VDOT
        "repetition": 1.05     # 105% of VDOT
    }
    
    training_paces = {}
    
    # Easy pace range
    easy_low_speed = vdot * pace_percentages["easy"][0] * 1000 / 60  # m/s
    easy_high_speed = vdot * pace_percentages["easy"][1] * 1000 / 60  # m/s
    easy_low_pace = meters_per_second_to_pace(easy_high_speed)
    easy_high_pace = meters_per_second_to_pace(easy_low_speed)
    
    training_paces["easy"] = {
        "pace_per_km": f"{easy_low_pace}-{easy_high_pace}",
        "description": "Conversational pace for base building",
        "heart_rate_range": "65-79% of max HR"
    }
    
    # Other paces
    for pace_type, percentage in pace_percentages.items():
        if pace_type != "easy":
            speed_mps = vdot * percentage * 1000 / 60  # m/s
            pace = meters_per_second_to_pace(speed_mps)
            
            descriptions = {
                "marathon": ("Marathon race pace", "80-89% of max HR"),
                "threshold": ("Comfortably hard, sustainable for ~1 hour", "88-92% of max HR"),
                "interval": ("3-5 minute intervals at 3K-5K pace", "95-100% of max HR"),
                "repetition": ("Short, fast repeats for speed development", "Not HR based - focus on pace")
            }
            
            desc, hr_range = descriptions[pace_type]
            training_paces[pace_type] = {
                "pace_per_km": pace,
                "description": desc,
                "heart_rate_range": hr_range
            }
    
    return training_paces

def clear_cache():
    """Clear all cached data."""
    global _cache
    _cache = {}
    logger.info("Cache cleared")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    valid_entries = sum(1 for entry in _cache.values() if datetime.now() < entry['expires_at'])
    expired_entries = len(_cache) - valid_entries
    
    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
        "cache_keys": list(_cache.keys())
    }
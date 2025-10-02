#!/usr/bin/env python3
"""Utility functions and decorators for Garmin Connect MCP server."""

import asyncio
import base64
import functools
import json
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

# Cache duration configurations (in hours)
CACHE_DURATIONS = {
    # Static data - changes rarely
    "personal_records": 24.0,       # Personal records don't change often
    "race_predictions": 12.0,        # Based on fitness, changes slowly

    # Semi-dynamic data - changes daily
    "vo2max": 6.0,                  # VO2 Max updates daily but changes slowly
    "training_status": 1.0,          # Training status updates hourly
    "training_readiness": 1.0,       # Readiness changes throughout the day
    "endurance_score": 1.0,          # Endurance score
    "hill_score": 1.0,               # Hill score

    # Dynamic data - changes frequently
    "heart_rate": 0.25,              # Heart rate changes rapidly (15 mins)
    "stress": 0.25,                  # Stress levels change rapidly (15 mins)
    "body_battery": 0.5,             # Body battery updates every 30 mins
    "hrv": 0.5,                      # HRV data changes frequently

    # Activity data
    "activities": 0.5,               # Recent activities might be added
    "activity_details": 24.0,        # Past activity details don't change

    # Health metrics
    "sleep": 2.0,                    # Sleep data is stable after wake up
    "respiration": 1.0,              # Respiration data updates hourly
    "spo2": 2.0,                     # SpO2 changes slowly

    # Default
    "default": 1.0                   # Default cache duration
}

# Cache storage
_cache: Dict[str, Dict[str, Any]] = {}

class GarminAPIError(Exception):
    """Base exception for Garmin API errors."""
    pass

class GarminAuthenticationError(GarminAPIError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)

class GarminNetworkError(GarminAPIError):
    """Raised when network-related errors occur."""
    def __init__(self, message: str = "Network error occurred"):
        self.message = message
        super().__init__(self.message)

class GarminDataNotFoundError(GarminAPIError):
    """Raised when requested data is not available."""
    def __init__(self, message: str = "Requested data not found"):
        self.message = message
        super().__init__(self.message)

class GarminRateLimitError(GarminAPIError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)

class GarminDeviceRequiredError(GarminAPIError):
    """Raised when specific device capabilities are required."""
    def __init__(self, message: str = "Compatible Garmin device required"):
        self.message = message
        super().__init__(self.message)

def handle_api_errors(func: F) -> F:
    """Decorator to handle API errors with detailed categorization."""
    @functools.wraps(func)
    async def wrapper(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await func(self, args)
        except GarminAPIError as e:
            # Already categorized error
            logger.error(f"{func.__name__} failed with {e.__class__.__name__}: {str(e)}")
            return {
                "error": str(e),
                "error_type": e.__class__.__name__,
                "user_message": _get_user_friendly_message(e)
            }
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"{func.__name__} failed: {str(e)}")

            # Categorize the error
            if "401" in error_msg or "unauthorized" in error_msg or "authentication" in error_msg:
                return {
                    "error": "Authentication failed",
                    "error_type": "GarminAuthenticationError",
                    "user_message": "Please check your Garmin Connect credentials or re-authenticate"
                }
            elif "404" in error_msg or "not found" in error_msg:
                return {
                    "error": "Data not found",
                    "error_type": "GarminDataNotFoundError",
                    "user_message": "The requested data is not available. Please ensure your device is syncing properly"
                }
            elif "429" in error_msg or "rate limit" in error_msg:
                return {
                    "error": "Rate limit exceeded",
                    "error_type": "GarminRateLimitError",
                    "user_message": "Too many requests. Please wait a moment before trying again"
                }
            elif "timeout" in error_msg or "connection" in error_msg or "network" in error_msg:
                return {
                    "error": "Network error",
                    "error_type": "GarminNetworkError",
                    "user_message": "Connection issue. Please check your network and try again"
                }
            elif "device" in error_msg or "not supported" in error_msg:
                return {
                    "error": "Device capability required",
                    "error_type": "GarminDeviceRequiredError",
                    "user_message": "This feature requires a compatible Garmin device with the necessary sensors"
                }
            else:
                return {
                    "error": f"API call failed: {str(e)}",
                    "error_type": "GarminAPIError",
                    "user_message": "An unexpected error occurred. Please try again later"
                }
    return wrapper

def _get_user_friendly_message(error: GarminAPIError) -> str:
    """Get user-friendly message for specific error types."""
    if isinstance(error, GarminAuthenticationError):
        return "Please check your Garmin Connect credentials or re-authenticate using the setup script"
    elif isinstance(error, GarminNetworkError):
        return "Connection issue. Please check your internet connection and try again"
    elif isinstance(error, GarminDataNotFoundError):
        return "The requested data is not available. Please ensure your Garmin device is syncing properly"
    elif isinstance(error, GarminRateLimitError):
        return "Too many requests. Please wait a few moments before trying again"
    elif isinstance(error, GarminDeviceRequiredError):
        return "This feature requires a compatible Garmin device with the necessary sensors"
    else:
        return "An error occurred while accessing Garmin Connect. Please try again"

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

def with_retry(max_attempts: int = 3, delay: float = 1.0, retry_on: Optional[List[type]] = None) -> Callable[[F], F]:
    """Decorator to retry failed API calls with intelligent retry strategy.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        retry_on: List of exception types to retry on (defaults to network/timeout errors)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Default retryable errors
            if retry_on is None:
                retryable = [GarminNetworkError, GarminRateLimitError, TimeoutError, ConnectionError]
            else:
                retryable = retry_on

            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if we should retry this error
                    should_retry = False
                    error_msg = str(e).lower()

                    # Check explicit exception types
                    if any(isinstance(e, exc_type) for exc_type in retryable):
                        should_retry = True
                    # Check error message patterns
                    elif any(pattern in error_msg for pattern in ["timeout", "connection", "network", "429", "rate limit"]):
                        should_retry = True
                    # Don't retry authentication or data not found errors
                    elif any(pattern in error_msg for pattern in ["401", "unauthorized", "authentication", "404", "not found"]):
                        should_retry = False

                    if not should_retry:
                        logger.debug(f"{func.__name__} failed with non-retryable error: {str(e)}")
                        raise

                    if attempt < max_attempts - 1:
                        # Use different backoff for rate limit errors
                        if "429" in error_msg or "rate limit" in error_msg:
                            wait_time = delay * (3 ** attempt)  # More aggressive backoff for rate limits
                        else:
                            wait_time = delay * (2 ** attempt)  # Normal exponential backoff

                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), retrying in {wait_time}s: {str(e)}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {str(e)}")

            raise last_exception
        return wrapper
    return decorator

def cached(cache_duration_hours: Optional[float] = None, cache_type: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to cache API responses with smart duration based on data type.

    Args:
        cache_duration_hours: Explicit cache duration in hours (overrides cache_type)
        cache_type: Type of data for automatic cache duration selection
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, args: Dict[str, Any]) -> Dict[str, Any]:
            # Determine cache duration
            if cache_duration_hours is not None:
                duration = cache_duration_hours
            elif cache_type:
                duration = CACHE_DURATIONS.get(cache_type, CACHE_DURATIONS["default"])
            else:
                # Try to infer from function name
                func_name = func.__name__.replace("_get_", "").replace("_", "")
                duration = CACHE_DURATIONS.get(func_name, CACHE_DURATIONS["default"])

            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(sorted(args.items()))}"

            # Check if cached result exists and is still valid
            if cache_key in _cache:
                cached_data = _cache[cache_key]
                if datetime.now() < cached_data['expires_at']:
                    logger.debug(f"Returning cached result for {func.__name__} (expires in {(cached_data['expires_at'] - datetime.now()).total_seconds() / 60:.1f} mins)")
                    return cached_data['data']

            # Call the actual function
            result = await func(self, args)

            # Cache the result if it's not an error
            if not (isinstance(result, dict) and 'error' in result):
                _cache[cache_key] = {
                    'data': result,
                    'expires_at': datetime.now() + timedelta(hours=duration)
                }
                logger.debug(f"Cached {func.__name__} for {duration} hours")

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

# ============================================================================
# Pagination Utilities (MCP Best Practice)
# ============================================================================

def encode_cursor(data: Dict[str, Any]) -> str:
    """
    Encode pagination data into an opaque cursor string.

    Args:
        data: Dictionary containing pagination state (offset, filters, etc.)

    Returns:
        Base64-encoded cursor string

    Example:
        >>> encode_cursor({"offset": 20, "date": "2025-01-01"})
        'eyJvZmZzZXQiOiAyMCwgImRhdGUiOiAiMjAyNS0wMS0wMSJ9'
    """
    try:
        json_str = json.dumps(data, separators=(',', ':'))
        return base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8').rstrip('=')
    except Exception as e:
        logger.error(f"Failed to encode cursor: {e}")
        return ""

def decode_cursor(cursor: str) -> Optional[Dict[str, Any]]:
    """
    Decode an opaque cursor string back into pagination data.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Dictionary containing pagination state, or None if invalid

    Example:
        >>> decode_cursor('eyJvZmZzZXQiOiAyMCwgImRhdGUiOiAiMjAyNS0wMS0wMSJ9')
        {"offset": 20, "date": "2025-01-01"}
    """
    if not cursor:
        return None

    try:
        # Add padding if needed
        padding = 4 - (len(cursor) % 4)
        if padding != 4:
            cursor += '=' * padding

        decoded = base64.urlsafe_b64decode(cursor.encode('utf-8'))
        return json.loads(decoded.decode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to decode cursor: {e}")
        return None

def create_pagination_response(
    items: List[Any],
    cursor_data: Optional[Dict[str, Any]],
    page_size: int,
    has_more: bool = None
) -> Dict[str, Any]:
    """
    Create a standardized pagination response following MCP best practices.

    Args:
        items: List of items for current page
        cursor_data: Data for the next cursor (e.g., {"offset": 20})
        page_size: Number of items per page
        has_more: Whether there are more items (auto-detected if None)

    Returns:
        Dictionary with items and pagination metadata

    Example:
        >>> create_pagination_response(
        ...     items=[...],
        ...     cursor_data={"offset": 20},
        ...     page_size=20
        ... )
        {
            "items": [...],
            "pagination": {
                "returned": 20,
                "nextCursor": "eyJvZmZzZXQiOjIwfQ",
                "hasMore": true
            }
        }
    """
    if has_more is None:
        has_more = len(items) == page_size

    response = {
        "items": items,
        "pagination": {
            "returned": len(items),
            "hasMore": has_more
        }
    }

    if has_more and cursor_data:
        response["pagination"]["nextCursor"] = encode_cursor(cursor_data)

    return response

# ============================================================================
# Response Size Management (MCP Tool Response Limit: 1MB)
# ============================================================================

def estimate_json_size(data: Any) -> int:
    """
    Estimate the size of data after JSON serialization.

    Args:
        data: Any JSON-serializable data

    Returns:
        Estimated size in bytes
    """
    try:
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return len(json_str.encode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to estimate JSON size: {e}")
        return 0

def is_large_field(key: str, value: Any, threshold_bytes: int = 100_000) -> bool:
    """
    Check if a field contains large data that should be moved to Resources.

    Args:
        key: Field name
        value: Field value
        threshold_bytes: Size threshold (default 100KB)

    Returns:
        True if field is large and should be moved
    """
    # Check by field name pattern
    large_field_patterns = [
        'raw_', 'full_', 'detailed_', 'complete_',
        'activity_details', 'metric_descriptors',
        'activity_detail_metrics', 'gps_', 'chart_'
    ]

    if any(pattern in key.lower() for pattern in large_field_patterns):
        if value is not None:
            size = estimate_json_size(value)
            return size > threshold_bytes

    return False

def split_large_response(
    data: Dict[str, Any],
    max_size_bytes: int = 800_000,
    create_resource_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Split large response by moving big fields to Resources.

    Args:
        data: Response data
        max_size_bytes: Maximum response size (default 800KB)
        create_resource_callback: Function to create resource URI for overflow data

    Returns:
        Modified response with large fields replaced by Resource URIs
    """
    current_size = estimate_json_size(data)

    if current_size <= max_size_bytes:
        return data  # No need to split

    logger.info(f"Response size ({current_size} bytes) exceeds limit ({max_size_bytes} bytes), splitting...")

    result = {}
    overflow_fields = {}

    for key, value in data.items():
        if is_large_field(key, value, threshold_bytes=50_000):
            # Move to overflow
            overflow_fields[key] = value

            # Create resource URI if callback provided
            if create_resource_callback:
                resource_uri = create_resource_callback(key, value)
                result[f"{key}_resource"] = resource_uri
                result[f"{key}_note"] = f"Data moved to resource due to size. Use {resource_uri} to access."
            else:
                result[f"{key}_omitted"] = f"Field omitted due to size ({estimate_json_size(value)} bytes)"
        else:
            result[key] = value

    # Add metadata
    if overflow_fields:
        result["_overflow_info"] = {
            "fields_moved": list(overflow_fields.keys()),
            "original_size_bytes": current_size,
            "reduced_size_bytes": estimate_json_size(result)
        }

    return result

def response_size_guard(max_bytes: int = 800_000):
    """
    Decorator to automatically guard against large tool responses.

    Usage:
        @response_size_guard(max_bytes=800_000)
        async def my_tool(self, args):
            return large_data
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, args: Dict[str, Any]) -> Dict[str, Any]:
            result = await func(self, args)

            # Check response size
            size = estimate_json_size(result)

            if size > max_bytes:
                logger.warning(f"{func.__name__} response size ({size} bytes) exceeds limit ({max_bytes} bytes)")

                # Try to split
                create_resource = getattr(self, '_create_overflow_resource', None)
                result = split_large_response(result, max_bytes, create_resource)

                final_size = estimate_json_size(result)
                logger.info(f"Response reduced from {size} to {final_size} bytes")

            return result
        return wrapper
    return decorator
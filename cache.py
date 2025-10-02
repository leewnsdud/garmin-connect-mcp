#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from utils import estimate_json_size

logger = logging.getLogger(__name__)


class OverflowDataCache:
    """
    Cache for large data that cannot fit in tool responses.
    Provides Resource URIs for accessing overflow data.
    """
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_lock = asyncio.Lock()

    @classmethod
    async def store(cls, activity_id: str, field_name: str, data: Any, ttl_seconds: int = 3600) -> str:
        """
        Store overflow data and return a Resource URI.

        Args:
            activity_id: Activity ID for namespacing
            field_name: Field name (e.g., 'raw_details', 'full_data')
            data: Data to store
            ttl_seconds: Time to live in seconds

        Returns:
            Resource URI to access the data
        """
        async with cls._cache_lock:
            import uuid
            cache_id = f"{activity_id}_{field_name}_{uuid.uuid4().hex[:8]}"

            cls._cache[cache_id] = {
                'data': data,
                'expires_at': datetime.now() + timedelta(seconds=ttl_seconds),
                'activity_id': activity_id,
                'field_name': field_name
            }

            logger.info(f"Stored overflow data: {cache_id} (size: {estimate_json_size(data)} bytes)")

            return f"overflow://{cache_id}"

    @classmethod
    async def get(cls, cache_id: str) -> Optional[Any]:
        """
        Retrieve overflow data by cache ID.

        Args:
            cache_id: Cache ID from URI

        Returns:
            Stored data or None if not found/expired
        """
        async with cls._cache_lock:
            entry = cls._cache.get(cache_id)

            if not entry:
                logger.warning(f"Overflow data not found: {cache_id}")
                return None

            if datetime.now() > entry['expires_at']:
                logger.info(f"Overflow data expired: {cache_id}")
                del cls._cache[cache_id]
                return None

            return entry['data']

    @classmethod
    async def cleanup_expired(cls):
        """Remove expired cache entries."""
        async with cls._cache_lock:
            now = datetime.now()
            expired = [k for k, v in cls._cache.items() if now > v['expires_at']]

            for key in expired:
                del cls._cache[key]

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired overflow entries")

#!/usr/bin/env python3
"""Service layer responsible for managing Garmin client authentication and data access."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from garminconnect import Garmin
from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

logger = logging.getLogger(__name__)


class GarminClientService:
    """Encapsulates Garmin Connect client lifecycle, authentication, and helpers."""

    def __init__(self) -> None:
        self._client: Optional[Garmin] = None
        self._auth_lock = asyncio.Lock()
        self._last_auth_time: Optional[datetime] = None
        self._cached_training_plans: Optional[Dict[str, Any]] = None
        self._training_plans_cached_at: Optional[datetime] = None

    # ---------------------------------------------------------------------
    # Authentication lifecycle
    # ---------------------------------------------------------------------
    async def ensure_authenticated(self, username: str, password: str) -> Garmin:
        """Ensure Garmin client is authenticated and ready for use."""
        async with self._auth_lock:
            if self._client is None or self._should_reauthenticate():
                await self._authenticate(username, password)
                self._last_auth_time = datetime.now()
        return self._client  # type: ignore[return-value]

    def reset(self) -> None:
        """Reset client state so next call will trigger re-authentication."""
        self._client = None
        self._last_auth_time = None
        self._cached_training_plans = None
        self._training_plans_cached_at = None

    def _should_reauthenticate(self) -> bool:
        if self._last_auth_time is None:
            return True
        hours_since_auth = (datetime.now() - self._last_auth_time).total_seconds() / 3600
        return hours_since_auth > 6

    async def _authenticate(self, username: str, password: str) -> None:
        if not username or not password:
            raise ValueError(
                "Authentication failed. Please ensure GARMIN_USERNAME and GARMIN_PASSWORD are set in environment variables."
            )

        if self._client is None:
            self._client = Garmin(email=username, password=password)
            logger.debug("Created new Garmin client instance")

        tokenstore = os.path.expanduser("~/.garminconnect")
        try:
            result = await asyncio.to_thread(self._client.login, tokenstore)
            logger.info("Successfully authenticated with stored tokens")
            await self._verify_connection()
        except FileNotFoundError:
            logger.info("Token store not found; attempting credential login")
            await self._credential_login(username, password)
        except Exception as token_error:  # noqa: BLE001 - handled specifically below
            logger.info("Token login failed: %s", token_error)
            await self._credential_login(username, password)

    async def _credential_login(self, username: str, password: str) -> None:
        assert self._client is not None

        try:
            result = await asyncio.to_thread(self._client.login)
            if result is True or isinstance(result, tuple):
                logger.info("Successfully authenticated with credentials")
                await self._verify_connection()
            elif isinstance(result, dict):
                raise ValueError(
                    "Multi-factor authentication required. Disable 2FA temporarily or use setup script."
                )
            else:
                raise ValueError(f"Unexpected login result: {result}")
        except GarminConnectAuthenticationError:
            raise
        except GarminConnectTooManyRequestsError:
            raise
        except GarminConnectConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001 - propagate as connection error
            logger.exception("Credential login failed")
            raise GarminConnectConnectionError(f"Login failed: {exc}") from exc

    async def _verify_connection(self) -> None:
        assert self._client is not None
        try:
            await asyncio.to_thread(self._client.get_full_name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Connection verification failed: %s", exc)
            raise GarminConnectConnectionError("Failed to verify Garmin Connect session") from exc

    # ---------------------------------------------------------------------
    # Training plan helpers with lightweight caching
    # ---------------------------------------------------------------------
    async def load_training_plans(self) -> Dict[str, Any]:
        await self.ensure_authenticated_from_env()
        if (
            self._cached_training_plans is not None
            and self._training_plans_cached_at
            and datetime.now() - self._training_plans_cached_at < timedelta(minutes=30)
        ):
            return self._cached_training_plans

        assert self._client is not None
        plans = await asyncio.to_thread(self._client.get_training_plans)
        self._cached_training_plans = plans or {}
        self._training_plans_cached_at = datetime.now()
        return self._cached_training_plans

    async def fetch_training_plan_detail(
        self,
        plan_id: int,
        plans_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self.ensure_authenticated_from_env()
        plans_data = plans_response or await self.load_training_plans()
        plan_list = plans_data.get("trainingPlanList") or []

        plan_category = None
        plan_name = None
        for plan in plan_list:
            if not isinstance(plan, dict):
                continue
            try:
                current_id = int(plan.get("trainingPlanId"))
            except (TypeError, ValueError):
                continue
            if current_id == plan_id:
                plan_category = plan.get("trainingPlanCategory")
                plan_name = plan.get("name")
                break

        assert self._client is not None
        fetcher = self._client.get_training_plan_by_id
        if plan_category == "FBT_ADAPTIVE":
            fetcher = self._client.get_adaptive_training_plan_by_id

        try:
            plan_detail = await asyncio.to_thread(fetcher, plan_id)
        except Exception as primary_error:  # noqa: BLE001
            if fetcher is self._client.get_adaptive_training_plan_by_id:
                logger.error("Failed to retrieve adaptive training plan %s: %s", plan_id, primary_error)
                raise

            logger.debug(
                "Standard training plan fetch failed for %s, retrying adaptive endpoint: %s",
                plan_id,
                primary_error,
            )
            plan_detail = await asyncio.to_thread(
                self._client.get_adaptive_training_plan_by_id,
                plan_id,
            )
            plan_category = plan_category or "FBT_ADAPTIVE"

        return {
            "detail": plan_detail or {},
            "metadata": {
                "plan_category": plan_category,
                "plan_name": plan_name,
            },
            "plans_response": plans_data,
        }

    # ---------------------------------------------------------------------
    # Convenience helpers
    # ---------------------------------------------------------------------
    async def ensure_authenticated_from_env(self) -> Garmin:
        username = os.getenv("GARMIN_USERNAME")
        password = os.getenv("GARMIN_PASSWORD")
        return await self.ensure_authenticated(username or "", password or "")

    @property
    def client(self) -> Garmin:
        if self._client is None:
            raise GarminConnectConnectionError("Garmin client is not authenticated")
        return self._client
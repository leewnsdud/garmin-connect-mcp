#!/usr/bin/env python3
"""Test helpers for stubbing external modules."""

from __future__ import annotations

import sys
import types
from contextlib import asynccontextmanager


def ensure_garmin_module_stub() -> None:
    if "garminconnect" in sys.modules:
        return

    stub = types.ModuleType("garminconnect")

    class _StubGarmin:
        pass

    class _StubError(Exception):
        pass

    stub.Garmin = _StubGarmin
    stub.GarminConnectAuthenticationError = _StubError
    stub.GarminConnectConnectionError = _StubError
    stub.GarminConnectTooManyRequestsError = _StubError

    sys.modules["garminconnect"] = stub


def ensure_mcp_module_stub() -> None:
    if "mcp" in sys.modules:
        return

    mcp_pkg = types.ModuleType("mcp")

    class _StubServer:
        def __init__(self, *_args, **_kwargs):
            pass

        def list_resources(self):
            def decorator(func):
                return func

            return decorator

        def read_resource(self):
            def decorator(func):
                return func

            return decorator

        def list_tools(self):
            def decorator(func):
                return func

            return decorator

        def call_tool(self):
            def decorator(func):
                return func

            return decorator

        def get_capabilities(self, **_kwargs):
            return {}

        async def run(self, *_args, **_kwargs):
            return None

    class _NotificationOptions:
        pass

    server_module = types.ModuleType("mcp.server")
    server_module.Server = _StubServer
    server_module.NotificationOptions = _NotificationOptions

    models_module = types.ModuleType("mcp.server.models")

    class _InitializationOptions:
        def __init__(self, **_kwargs):
            pass

    models_module.InitializationOptions = _InitializationOptions

    @asynccontextmanager
    async def stdio_server():
        yield (None, None)

    stdio_module = types.ModuleType("mcp.server.stdio")
    stdio_module.stdio_server = stdio_server

    types_module = types.ModuleType("mcp.types")

    class _BaseType:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _TextContent:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    types_module.Resource = _BaseType
    types_module.Tool = _BaseType
    types_module.TextContent = _TextContent

    sys.modules["mcp"] = mcp_pkg
    sys.modules["mcp.server"] = server_module
    sys.modules["mcp.server.models"] = models_module
    sys.modules["mcp.server.stdio"] = stdio_module
    sys.modules["mcp.types"] = types_module

    mcp_pkg.server = server_module
    mcp_pkg.types = types_module


def ensure_test_stubs() -> None:
    """Ensure all external modules used by tests are stubbed."""
    ensure_garmin_module_stub()
    ensure_mcp_module_stub()


__all__ = [
    "ensure_garmin_module_stub",
    "ensure_mcp_module_stub",
    "ensure_test_stubs",
]


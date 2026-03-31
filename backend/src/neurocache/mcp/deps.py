"""Lifespan and dependency management for the MCP server."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


@asynccontextmanager
async def mcp_lifespan(server: FastMCP[dict[str, Any]]) -> AsyncIterator[dict[str, Any]]:
    """Initialize and validate MCP server dependencies at startup.

    Reads NEUROCACHE_USER_ID from settings, validates the user exists,
    and provides shared resources (user_id, openai_client) to all tool
    calls via the lifespan context.

    If NEUROCACHE_USER_ID is not set, the server starts but tools will
    return an error message. This prevents the MCP lifespan from crashing
    the entire FastAPI app when mounted via HTTP.
    """
    # Read user ID directly from environment to avoid issues with Settings
    # lru_cache potentially caching a stale value from an earlier import.
    user_id = os.environ.get("NEUROCACHE_USER_ID")

    if not user_id:
        logger.warning(
            "NEUROCACHE_USER_ID not set — MCP tools will be unavailable. "
            "Set it in your .env file or environment to enable MCP access."
        )
        yield {"user_id": None, "openai_client": None}
        return

    # Defer imports that trigger module-level side effects (e.g., AsyncOpenAI()
    # requires OPENAI_API_KEY at import time in dependencies/openai.py)
    from neurocache.dependencies.db import get_async_sqlalchemy_session
    from neurocache.dependencies.openai import get_openai_client
    from neurocache.models.user import User

    openai_client = get_openai_client()

    # Validate user exists using a short-lived session
    try:
        async with get_async_sqlalchemy_session() as db:
            if not await User.exists(db, user_id):
                logger.error(f"MCP: User '{user_id}' not found in the database.")
                yield {"user_id": None, "openai_client": None}
                return
    except Exception:
        logger.exception("MCP: Failed to validate user — database may be unavailable")
        yield {"user_id": None, "openai_client": None}
        return

    logger.info(f"MCP server started for user {user_id}")
    yield {"user_id": user_id, "openai_client": openai_client}
    logger.info("MCP server shutting down")

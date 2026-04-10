"""Hooks for the neurocache chat agent.

Tool bodies should return structured ``{"error": ...}`` payloads for
anticipated failures. This module is the safety net for *unanticipated*
exceptions — anything that bubbles out of a tool body would otherwise
crash the Vercel AI SDK stream mid-response. ``_recover_tool_error``
intercepts those, logs the traceback, and returns a structured recovery
payload so the agent can explain the failure to the user conversationally.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic_ai import ToolDefinition
from pydantic_ai.capabilities import Hooks
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.tools import RunContext

from neurocache.agents.deps import AgentDeps

logger = logging.getLogger(__name__)


def _recovery_payload(tool_name: str, error: Exception) -> dict[str, Any]:
    return {
        "error": "tool_failed",
        "tool": tool_name,
        "exception_type": type(error).__name__,
        "message": (
            f"The {tool_name} tool failed unexpectedly ({type(error).__name__}). "
            "Apologize to the user, explain briefly what you were trying to do, "
            "and suggest they retry or rephrase."
        ),
    }


async def _recover_tool_error(
    ctx: RunContext[AgentDeps],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: Any,
    error: Exception,
) -> dict[str, Any]:
    logger.exception(f"Unhandled exception in tool {tool_def.name}: {error!r}")
    return _recovery_payload(tool_def.name, error)


def build_chat_agent_hooks() -> Hooks[AgentDeps]:
    return Hooks[AgentDeps](tool_execute_error=_recover_tool_error)

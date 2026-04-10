from __future__ import annotations

import asyncio

from pydantic_ai import ToolDefinition
from pydantic_ai.capabilities import Hooks
from pydantic_ai.messages import ToolCallPart

from neurocache.agents.hooks import (
    _recover_tool_error,
    _recovery_payload,
    build_chat_agent_hooks,
)


class TestRecoveryPayload:
    def test_contains_tool_and_exception_type(self) -> None:
        payload = _recovery_payload("search_knowledge_base", RuntimeError("boom"))
        assert payload["error"] == "tool_failed"
        assert payload["tool"] == "search_knowledge_base"
        assert payload["exception_type"] == "RuntimeError"
        assert "search_knowledge_base" in payload["message"]

    def test_payload_shape_is_stable_across_exception_types(self) -> None:
        payload_a = _recovery_payload("search_knowledge_base", ValueError("bad"))
        payload_b = _recovery_payload("search_knowledge_base", ConnectionError("net"))
        assert payload_a.keys() == payload_b.keys()
        assert payload_a["exception_type"] == "ValueError"
        assert payload_b["exception_type"] == "ConnectionError"


class TestRecoverToolErrorHandler:
    def test_returns_recovery_payload_for_unexpected_exception(self) -> None:
        call = ToolCallPart(tool_name="search_knowledge_base", tool_call_id="call-1")
        tool_def = ToolDefinition(name="search_knowledge_base")

        async def _invoke() -> dict[str, object]:
            return await _recover_tool_error(
                None,  # type: ignore[arg-type]  # handler doesn't touch ctx
                call=call,
                tool_def=tool_def,
                args={},
                error=RuntimeError("db unreachable"),
            )

        result = asyncio.run(_invoke())
        assert result["error"] == "tool_failed"
        assert result["tool"] == "search_knowledge_base"
        assert result["exception_type"] == "RuntimeError"


class TestBuildChatAgentHooks:
    def test_returns_hooks_instance(self) -> None:
        hooks = build_chat_agent_hooks()
        assert isinstance(hooks, Hooks)

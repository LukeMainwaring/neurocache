"""Utilities for serializing/deserializing Pydantic AI ModelMessage objects.

Handles the round-trip between Pydantic AI ModelMessage format (used by agents),
storage format (JSONB dicts in PostgreSQL), and frontend format (Vercel AI UIMessage).
Also manages RAG source metadata attachment across all three formats.
"""

from typing import Any

from pydantic_ai.messages import BuiltinToolReturnPart, ModelMessage, ModelMessagesTypeAdapter, ModelResponse
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_ai.ui.vercel_ai.request_types import TextUIPart, UIMessage

# Type alias for RAG source metadata
# Contains: path, similarity, content, content_type, section_header, author,
# page_number (for PDFs), chapter (for PDFs)
RAGSource = dict[str, str | float | int]

# Type alias for web search source metadata
WebSource = dict[str, str]


# ============================================================================
# Request Parsing
# ============================================================================


def extract_latest_user_text(messages: list[UIMessage]) -> str:
    """Extract text content from the last user message in a Vercel AI request.

    Args:
        messages: List of UIMessage objects from the parsed request

    Returns:
        The text content of the last user message, or empty string if not found
    """
    for msg in reversed(messages):
        if msg.role == "user":
            for part in msg.parts:
                if isinstance(part, TextUIPart):
                    return part.text
    return ""


# ============================================================================
# Source Extraction
# ============================================================================


def extract_web_sources(messages: list[ModelMessage]) -> list[WebSource]:
    """Extract web source URLs from web search tool return parts in a conversation.

    Scans all model response messages for builtin web_search tool returns and
    extracts source URLs and titles.

    Args:
        messages: Full conversation messages from result.all_messages()

    Returns:
        List of web source dicts with 'url' and optional 'title' keys
    """
    sources: list[WebSource] = []
    for msg in messages:
        if isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, BuiltinToolReturnPart) and part.tool_name == "web_search":
                    sources.extend(_extract_web_sources_from_content(part.content))
    return sources


def _extract_web_sources_from_content(content: Any) -> list[WebSource]:
    """Extract web source URLs from a single web search tool return content.

    Content shape: {"status": "completed", "sources": [{"type": "url", "url": "..."}]}
    Some returns have no sources (just {"status": "completed"}).
    """
    sources: list[WebSource] = []
    if isinstance(content, dict):
        for item in content.get("sources", []):
            if isinstance(item, dict) and "url" in item:
                source: WebSource = {"url": item["url"]}
                if "title" in item:
                    source["title"] = item["title"]
                sources.append(source)
    return sources


# ============================================================================
# Storage Serialization (write path)
# ============================================================================


def prepare_messages_for_storage(
    messages: list[ModelMessage],
    rag_sources: list[RAGSource] | None = None,
    web_sources: list[WebSource] | None = None,
) -> list[dict[str, Any]]:
    """Prepare messages for storage with optional source metadata.

    Converts Pydantic AI messages to storage format and attaches RAG/web sources
    to the last user request message for frontend display.

    Args:
        messages: List of Pydantic AI messages (full conversation from result.all_messages())
        rag_sources: Optional list of source metadata from RAG retrieval
        web_sources: Optional list of web search source metadata

    Returns:
        List of serialized message dicts ready for storage
    """
    serialized: list[dict[str, Any]] = ModelMessagesTypeAdapter.dump_python(messages, mode="json")

    if not serialized:
        return serialized

    # Attach sources to the last user-prompt request message.
    # With tool use, result.all_messages() may contain tool-return requests
    # (kind="request" with part_kind="tool-return") — we need the actual
    # user message (kind="request" with a "user-prompt" part).
    if rag_sources or web_sources:
        for msg in reversed(serialized):
            if msg.get("kind") == "request":
                parts = msg.get("parts", [])
                if any(p.get("part_kind") == "user-prompt" for p in parts):
                    if rag_sources:
                        msg["rag_sources"] = rag_sources
                    if web_sources:
                        msg["web_sources"] = web_sources
                    break

    return serialized


# ============================================================================
# Storage Deserialization (read path)
# ============================================================================


def deserialize_messages(message_data: list[dict[str, Any]]) -> list[ModelMessage]:
    """Deserialize stored messages back to ModelMessage format for agent use.

    Strips any extra fields we added (like rag_sources) before deserializing,
    since Pydantic AI's type adapter uses strict validation.

    Args:
        message_data: List of dictionaries from JSONB column

    Returns:
        List of ModelMessage objects (ModelRequest or ModelResponse)
    """
    cleaned: list[dict[str, Any]] = []
    for msg in message_data:
        clean_msg = {k: v for k, v in msg.items() if k not in ("rag_sources", "web_sources")}
        cleaned.append(clean_msg)

    return ModelMessagesTypeAdapter.validate_python(cleaned)


def messages_to_frontend(raw_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert stored messages to frontend-compatible Vercel AI UIMessage format.

    Deserializes raw storage dicts → ModelMessages → UIMessages, then re-attaches
    RAG source metadata (stored as an extra field on request messages) onto the
    corresponding frontend user messages.

    Args:
        raw_messages: List of raw message dicts from database JSONB column

    Returns:
        List of frontend-compatible message dicts with RAG metadata attached
    """
    model_messages = deserialize_messages(raw_messages)
    ui_messages = VercelAIAdapter.dump_messages(model_messages)
    frontend_messages: list[dict[str, Any]] = [msg.model_dump(mode="json", by_alias=True) for msg in ui_messages]

    # Re-attach source metadata from raw storage onto user messages.
    # Raw messages contain multiple "request" kinds — both user-prompt requests
    # and tool-return requests. Only user-prompt requests map to frontend user
    # messages, so skip tool-return requests to keep alignment correct.
    raw_request_idx = 0
    for fm in frontend_messages:
        if fm["role"] == "user":
            while raw_request_idx < len(raw_messages):
                msg = raw_messages[raw_request_idx]
                if msg.get("kind") == "request" and any(
                    p.get("part_kind") == "user-prompt" for p in msg.get("parts", [])
                ):
                    break
                raw_request_idx += 1
            if raw_request_idx < len(raw_messages):
                raw_msg = raw_messages[raw_request_idx]
                rag_sources = raw_msg.get("rag_sources")
                web_sources = raw_msg.get("web_sources")
                if rag_sources or web_sources:
                    fm.setdefault("metadata", {})
                    if fm["metadata"] is None:
                        fm["metadata"] = {}
                    if rag_sources:
                        fm["metadata"]["ragSources"] = rag_sources
                    if web_sources:
                        fm["metadata"]["webSources"] = web_sources
                raw_request_idx += 1

    return frontend_messages

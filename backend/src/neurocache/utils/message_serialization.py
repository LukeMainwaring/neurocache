"""Utilities for serializing/deserializing Pydantic AI ModelMessage objects."""

from typing import Any

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

# Type alias for RAG source metadata
# Contains: path, similarity, content, content_type, section_header, author,
# page_number (for PDFs), chapter (for PDFs)
RAGSource = dict[str, str | float | int]


def prepare_messages_for_storage(
    messages: list[ModelMessage],
    rag_sources: list[RAGSource] | None = None,
) -> list[dict[str, Any]]:
    """Prepare messages for storage with optional RAG source metadata.

    Converts Pydantic AI messages to storage format and attaches RAG sources
    to the last user request message for frontend display.

    Args:
        messages: List of Pydantic AI messages (full conversation from result.all_messages())
        rag_sources: Optional list of source metadata from RAG retrieval

    Returns:
        List of serialized message dicts ready for storage
    """
    serialized: list[dict[str, Any]] = ModelMessagesTypeAdapter.dump_python(messages, mode="json")

    if not serialized:
        return serialized

    # Attach RAG sources to the last user request message
    if rag_sources:
        for msg in reversed(serialized):
            if msg.get("kind") == "request":
                msg["rag_sources"] = rag_sources
                break

    return serialized


def deserialize_messages(message_data: list[dict[str, Any]]) -> list[ModelMessage]:
    """Deserialize stored messages back to ModelMessage format for agent use.

    Strips any extra fields we added (like rag_sources) before deserializing,
    since Pydantic AI's type adapter uses strict validation.

    Args:
        message_data: List of dictionaries from JSONB column

    Returns:
        List of ModelMessage objects (ModelRequest or ModelResponse)
    """
    # Strip extra fields we added (rag_sources) before deserializing
    cleaned: list[dict[str, Any]] = []
    for msg in message_data:
        clean_msg = {k: v for k, v in msg.items() if k != "rag_sources"}
        cleaned.append(clean_msg)

    return ModelMessagesTypeAdapter.validate_python(cleaned)

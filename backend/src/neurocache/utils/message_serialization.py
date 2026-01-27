"""Utilities for serializing/deserializing Pydantic AI ModelMessage objects."""

from typing import Any

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

# Type alias for RAG source metadata
RAGSource = dict[str, str | float]


def prepare_messages_for_storage(
    messages: list[ModelMessage],
    original_query: str,
    rag_sources: list[RAGSource],
) -> list[dict[str, Any]]:
    """Prepare messages for storage with original query and RAG sources.

    Converts Pydantic AI messages to storage format, replacing the augmented
    query with the original and adding RAG sources as a simple extra field.

    Args:
        messages: List of Pydantic AI messages from result.new_messages()
        original_query: The user's original query before RAG augmentation
        rag_sources: List of source metadata from RAG retrieval

    Returns:
        List of serialized message dicts ready for storage
    """
    serialized: list[dict[str, Any]] = ModelMessagesTypeAdapter.dump_python(messages, mode="json")

    if not serialized:
        return serialized

    # First message is user request - replace augmented content with original
    first_msg = serialized[0]
    if first_msg.get("kind") == "request":
        parts = first_msg.get("parts", [])
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict) and part.get("part_kind") == "user-prompt":
                    part["content"] = original_query
                    break

        # Add RAG sources as simple extra field
        if rag_sources:
            first_msg["rag_sources"] = rag_sources

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

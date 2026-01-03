"""Utilities for serializing/deserializing Pydantic AI ModelMessage objects."""

from typing import Any, cast

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter


def serialize_messages(messages: list[ModelMessage]) -> list[dict[str, Any]]:
    """Serialize ModelMessage list to JSON-compatible format.

    Uses Pydantic AI's ModelMessagesTypeAdapter to properly serialize
    ModelRequest and ModelResponse objects (which are dataclasses, not Pydantic models).

    Args:
        messages: List of Pydantic AI ModelMessage objects (ModelRequest or ModelResponse)

    Returns:
        List of dictionaries suitable for JSONB storage
    """
    return cast(list[dict[str, Any]], ModelMessagesTypeAdapter.dump_python(messages, mode="json"))


def deserialize_messages(message_data: list[dict[str, Any]]) -> list[ModelMessage]:
    """Deserialize JSONB data back to ModelMessage list.

    Uses Pydantic AI's ModelMessagesTypeAdapter to properly validate and construct
    ModelRequest and ModelResponse objects from serialized data.

    Args:
        message_data: List of dictionaries from JSONB column

    Returns:
        List of ModelMessage objects (ModelRequest or ModelResponse)
    """
    return ModelMessagesTypeAdapter.validate_python(message_data)

"""Utilities for transforming messages between backend and frontend formats."""

import uuid
from typing import Any


def transform_messages_for_frontend(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transform stored ModelMessage format to frontend-compatible format.

    Converts PydanticAI ModelMessage format (ModelRequest/ModelResponse) to the
    format expected by the frontend Vercel AI SDK:
    {
        id: string,
        role: "user" | "assistant",
        parts: [{type: "text", text: string}]
    }

    Args:
        messages: List of serialized PydanticAI ModelMessages from database

    Returns:
        List of frontend-compatible message dictionaries
    """
    frontend_messages = []

    for msg in messages:
        # ModelRequest has 'parts' field with user content
        # ModelResponse has 'parts' field with assistant content
        kind = msg.get("kind")

        if kind == "request":
            # User message
            parts = msg.get("parts", [])
            content = ""

            # Extract text content from parts
            for part in parts:
                part_kind = part.get("part_kind")
                if part_kind == "user-prompt":
                    content = part.get("content", "")
                elif part_kind == "text":
                    content += part.get("content", "")

            frontend_messages.append(
                {
                    "id": str(uuid.uuid4()),  # Generate ID for frontend
                    "role": "user",
                    "parts": [{"type": "text", "text": content}],
                }
            )

        elif kind == "response":
            # Assistant message
            parts = msg.get("parts", [])
            content = ""

            # Extract text content from parts
            for part in parts:
                part_kind = part.get("part_kind")
                if part_kind == "text":
                    content += part.get("content", "")

            if content:  # Only add if there's actual content
                frontend_messages.append(
                    {
                        "id": str(uuid.uuid4()),  # Generate ID for frontend
                        "role": "assistant",
                        "parts": [{"type": "text", "text": content}],
                    }
                )

    return frontend_messages

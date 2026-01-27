"""Utilities for transforming messages between backend and frontend formats."""

import uuid
from typing import Any


def transform_messages_for_frontend(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transform stored messages to frontend-compatible format.

    Converts stored Pydantic AI message format to the format expected by
    the frontend Vercel AI SDK:
    {
        id: string,
        role: "user" | "assistant",
        parts: [{type: "text", text: string}],
        metadata?: { ragSources?: [...] }
    }

    Args:
        messages: List of stored message dicts from database

    Returns:
        List of frontend-compatible message dictionaries
    """
    frontend_messages = []

    for msg in messages:
        kind = msg.get("kind")

        if kind == "request":
            # User message - extract content from parts
            content = ""
            for part in msg.get("parts", []):
                if part.get("part_kind") == "user-prompt":
                    content = part.get("content", "")
                    break

            frontend_msg: dict[str, Any] = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"type": "text", "text": content}],
            }

            if msg.get("rag_sources"):
                frontend_msg["metadata"] = {"ragSources": msg["rag_sources"]}

            frontend_messages.append(frontend_msg)

        elif kind == "response":
            # Assistant message - extract text content
            content = ""
            for part in msg.get("parts", []):
                if part.get("part_kind") == "text":
                    content += part.get("content", "")

            if content:
                frontend_messages.append(
                    {
                        "id": str(uuid.uuid4()),
                        "role": "assistant",
                        "parts": [{"type": "text", "text": content}],
                    }
                )

    return frontend_messages

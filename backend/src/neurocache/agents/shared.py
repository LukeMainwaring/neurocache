"""Shared utilities for all agent modules.

This module provides common functionality used by both agents:
- Message history management
- Eval result formatting
"""

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic_ai.messages import ModelMessage
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.message import Message
from neurocache.models.thread import Thread
from neurocache.schemas.agent_type import AgentType
from neurocache.utils.message_serialization import deserialize_messages

logger = logging.getLogger(__name__)


async def get_history(db: AsyncSession, thread_id: str, agent_type: AgentType) -> list[ModelMessage]:
    """Get message history for a thread from database (for agent use).

    Args:
        db: Database session
        thread_id: The thread identifier
        agent_type: Agent type

    Returns:
        List of ModelMessage objects, or empty list if thread doesn't exist
    """
    message_data = await Message.get_history(db, thread_id, agent_type.value)
    if not message_data:
        return []
    return deserialize_messages(message_data)


async def save_new_messages(
    db: AsyncSession,
    thread_id: str,
    agent_type: AgentType,
    user_id: str,
    new_messages: list[dict[str, Any]],
) -> None:
    """Save new messages to thread history.

    Args:
        db: Database session
        thread_id: The thread identifier
        agent_type: Agent type
        user_id: User ID for thread creation
        new_messages: New messages as dicts (already prepared for storage)
    """
    # Ensure thread exists (implicit creation)
    await Thread.get_or_create(db, thread_id, agent_type.value, user_id)

    # Get existing messages and append new ones
    existing = await Message.get_history(db, thread_id, agent_type.value)
    all_messages = existing + new_messages

    await Message.save_history(db, thread_id, agent_type.value, all_messages)
    # Update thread timestamp
    thread = await Thread.get(db, thread_id, agent_type.value)
    if thread:
        thread.updated_at = datetime.now(timezone.utc)
        await db.flush()

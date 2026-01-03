"""Shared utilities for all agent modules.

This module provides common functionality used by both agents:
- Message history management
- Eval result formatting
"""

import logging
from datetime import datetime, timezone

from pydantic_ai import ModelMessage
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.message import Message
from neurocache.models.thread import Thread
from neurocache.schemas.agent_type import AgentType
from neurocache.utils.message_serialization import deserialize_messages, serialize_messages

logger = logging.getLogger(__name__)


async def get_history(db: AsyncSession, thread_id: str, agent_type: AgentType) -> list[ModelMessage]:
    """Get message history for a thread from database.

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


async def update_history(
    db: AsyncSession,
    thread_id: str,
    history: list[ModelMessage],
    agent_type: AgentType,
    user_id: str,
) -> None:
    """Update message history for a thread in database.

    Args:
        db: Database session
        thread_id: The thread identifier
        history: Updated list of ModelMessage objects
        agent_type: Agent type
        user_id: User ID for thread creation
    """
    # Ensure thread exists (implicit creation)
    await Thread.get_or_create(db, thread_id, agent_type.value, user_id)
    # Serialize and save messages
    serialized = serialize_messages(history)
    await Message.save_history(db, thread_id, agent_type.value, serialized)
    # Update thread timestamp
    thread = await Thread.get(db, thread_id, agent_type.value)
    if thread:
        thread.updated_at = datetime.now(timezone.utc)
        await db.flush()

"""Thread service functions."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.message import Message
from neurocache.models.thread import Thread
from neurocache.utils.message_serialization import messages_to_frontend


async def list_threads_for_user(
    db: AsyncSession,
    user_id: str,
    agent_type: str,
) -> list[Thread]:
    """List all threads for a user."""
    return await Thread.list_for_user(db, user_id, agent_type)


async def get_thread_messages(
    db: AsyncSession,
    thread_id: str,
    user_id: str,
    agent_type: str,
) -> list[dict[str, Any]]:
    """Get messages for a thread, validating ownership."""
    await Thread.get_for_user(db, thread_id, user_id, agent_type)
    raw = await Message.get_history(db, thread_id, agent_type)
    return messages_to_frontend(raw)


async def delete_thread(
    db: AsyncSession,
    thread_id: str,
    user_id: str,
    agent_type: str,
) -> None:
    """Delete a thread, validating ownership."""
    await Thread.get_for_user(db, thread_id, user_id, agent_type)
    await Thread.delete_for_user(db, thread_id, user_id, agent_type)


async def rename_thread(
    db: AsyncSession,
    thread_id: str,
    user_id: str,
    agent_type: str,
    title: str,
) -> Thread:
    """Rename a thread, validating ownership."""
    thread = await Thread.get_for_user(db, thread_id, user_id, agent_type)
    thread.title = title
    await db.flush()
    return thread

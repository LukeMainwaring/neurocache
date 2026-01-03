import logging

from fastapi import APIRouter, HTTPException

from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.models.message import Message
from neurocache.models.thread import Thread
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.thread_api import (
    ThreadListResponse,
    ThreadMessagesResponse,
    ThreadSummary,
)
from neurocache.utils.message_transformation import transform_messages_for_frontend

logger = logging.getLogger(__name__)

thread_router = APIRouter(prefix="/threads", tags=["threads"])


@thread_router.get("")
async def list_threads(db: AsyncPostgresSessionDep, user_id: AuthenticatedUser) -> ThreadListResponse:
    """List all threads for the authenticated user."""
    threads = await Thread.list_for_user(db, user_id, AgentType.CHAT.value)
    return ThreadListResponse(
        threads=[
            ThreadSummary(
                id=thread.thread_id,
                thread_id=thread.thread_id,
                title=f"Chat {thread.thread_id[:8]}",  # Placeholder title
                created_at=thread.created_at,
                updated_at=thread.updated_at,
            )
            for thread in threads
        ]
    )


@thread_router.get("/{thread_id}/messages")
async def get_thread_messages(
    db: AsyncPostgresSessionDep, thread_id: str, user_id: AuthenticatedUser
) -> ThreadMessagesResponse:
    """Get all messages for a specific thread."""
    thread = await Thread.get_for_user(db, thread_id, user_id, AgentType.CHAT.value)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    # Get messages and transform to frontend-compatible format
    messages = await Message.get_history(db, thread_id, AgentType.CHAT.value)
    frontend_messages = transform_messages_for_frontend(messages)

    return ThreadMessagesResponse(thread_id=thread_id, messages=frontend_messages)


@thread_router.delete("/{thread_id}")
async def delete_thread(db: AsyncPostgresSessionDep, thread_id: str, user_id: AuthenticatedUser) -> dict[str, str]:
    """Delete a thread and all its messages."""
    thread = await Thread.get_for_user(db, thread_id, user_id, AgentType.CHAT.value)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    await Thread.delete_for_user(db, thread_id, user_id, AgentType.CHAT.value)
    logger.info(f"Deleted thread {thread_id} for user {user_id}")
    return {"message": "Thread deleted successfully"}

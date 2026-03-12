import logging

from fastapi import APIRouter

from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.thread import (
    ThreadDeleteResponse,
    ThreadListResponse,
    ThreadMessagesResponse,
    ThreadRenameRequest,
    ThreadRenameResponse,
    ThreadSummary,
)
from neurocache.services import thread as thread_service

logger = logging.getLogger(__name__)

thread_router = APIRouter(prefix="/threads", tags=["threads"])


@thread_router.get("")
async def list_threads(db: AsyncPostgresSessionDep, user_id: AuthenticatedUser) -> ThreadListResponse:
    """List all threads for the authenticated user."""
    threads = await thread_service.list_threads_for_user(db, user_id, AgentType.CHAT.value)
    return ThreadListResponse(
        threads=[
            ThreadSummary(
                id=thread.thread_id,
                thread_id=thread.thread_id,
                title=thread.title,
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
    frontend_messages = await thread_service.get_thread_messages(db, thread_id, user_id, AgentType.CHAT.value)
    return ThreadMessagesResponse(thread_id=thread_id, messages=frontend_messages)


@thread_router.delete("/{thread_id}")
async def delete_thread(
    db: AsyncPostgresSessionDep, thread_id: str, user_id: AuthenticatedUser
) -> ThreadDeleteResponse:
    """Delete a thread and all its messages."""
    await thread_service.delete_thread(db, thread_id, user_id, AgentType.CHAT.value)
    logger.info(f"Deleted thread {thread_id} for user {user_id}")
    return ThreadDeleteResponse(message="Thread deleted successfully")


@thread_router.patch("/{thread_id}")
async def rename_thread(
    db: AsyncPostgresSessionDep,
    thread_id: str,
    user_id: AuthenticatedUser,
    body: ThreadRenameRequest,
) -> ThreadRenameResponse:
    """Rename a thread."""
    thread = await thread_service.rename_thread(db, thread_id, user_id, AgentType.CHAT.value, body.title)
    logger.info(f"Renamed thread {thread_id} for user {user_id}")
    return ThreadRenameResponse(thread_id=thread.thread_id, title=body.title)

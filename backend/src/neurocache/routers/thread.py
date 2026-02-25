import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.models.message import Message
from neurocache.models.thread import Thread
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.thread import (
    ThreadDeleteResponse,
    ThreadListResponse,
    ThreadMessagesResponse,
    ThreadSummary,
)
from neurocache.utils.message_serialization import deserialize_messages

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
    thread = await Thread.get_for_user(db, thread_id, user_id, AgentType.CHAT.value)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    # Get raw messages, deserialize to ModelMessages, convert to UIMessages
    raw = await Message.get_history(db, thread_id, AgentType.CHAT.value)
    model_messages = deserialize_messages(raw)
    ui_messages = VercelAIAdapter.dump_messages(model_messages)
    frontend_messages: list[dict[str, Any]] = [msg.model_dump(mode="json", by_alias=True) for msg in ui_messages]

    # Re-attach RAG source metadata from raw storage onto user messages
    raw_request_idx = 0
    for fm in frontend_messages:
        if fm["role"] == "user":
            # Walk raw messages to find the next request with rag_sources
            while raw_request_idx < len(raw) and raw[raw_request_idx].get("kind") != "request":
                raw_request_idx += 1
            if raw_request_idx < len(raw):
                rag_sources = raw[raw_request_idx].get("rag_sources")
                if rag_sources:
                    fm.setdefault("metadata", {})
                    if fm["metadata"] is None:
                        fm["metadata"] = {}
                    fm["metadata"]["ragSources"] = rag_sources
                raw_request_idx += 1

    return ThreadMessagesResponse(thread_id=thread_id, messages=frontend_messages)


@thread_router.delete("/{thread_id}")
async def delete_thread(
    db: AsyncPostgresSessionDep, thread_id: str, user_id: AuthenticatedUser
) -> ThreadDeleteResponse:
    """Delete a thread and all its messages."""
    thread = await Thread.get_for_user(db, thread_id, user_id, AgentType.CHAT.value)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    await Thread.delete_for_user(db, thread_id, user_id, AgentType.CHAT.value)
    logger.info(f"Deleted thread {thread_id} for user {user_id}")
    return ThreadDeleteResponse(message="Thread deleted successfully")

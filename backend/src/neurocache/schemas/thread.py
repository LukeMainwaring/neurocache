"""Thread schemas for conversation persistence."""

from datetime import datetime
from typing import Any

from pydantic import Field

from neurocache.schemas.agent_type import AgentType

from .base import BaseSchema


class ThreadSchema(BaseSchema):
    """Thread schema representing a conversation thread."""

    thread_id: str
    agent_type: AgentType
    user_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class ThreadCreateSchema(BaseSchema):
    """Schema for creating a new thread."""

    thread_id: str
    agent_type: AgentType
    user_id: str


class ThreadSummary(BaseSchema):
    """Summary of a thread for list view.

    Compatible with frontend sidebar expectations.
    """

    id: str  # Same as thread_id for compatibility
    thread_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime


class ThreadListResponse(BaseSchema):
    """Response containing list of threads."""

    threads: list[ThreadSummary]


class ThreadMessagesResponse(BaseSchema):
    """Response containing thread messages.

    Messages are returned in their raw JSONB format as stored in the database,
    which includes role, content, and metadata fields.
    """

    thread_id: str
    messages: list[dict[str, Any]]


class ThreadDeleteResponse(BaseSchema):
    """Response for successful thread delete operations."""

    message: str


class ThreadRenameRequest(BaseSchema):
    """Request to rename a thread."""

    title: str = Field(min_length=1, max_length=255)


class ThreadRenameResponse(BaseSchema):
    """Response for successful thread rename."""

    thread_id: str
    title: str

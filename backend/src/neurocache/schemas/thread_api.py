"""Thread API response schemas.

These schemas define the response format for thread management endpoints
that are consumed by the frontend.
"""

from datetime import datetime
from typing import Any

from .base import BaseSchema


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

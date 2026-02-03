"""Pydantic schemas for knowledge sources."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from ..base import BaseSchema


class KnowledgeSourceType(StrEnum):
    """Type of knowledge source."""

    OBSIDIAN = "obsidian"
    NOTION = "notion"
    LOCAL_FOLDER = "local_folder"


class KnowledgeSourceStatus(StrEnum):
    """Status of a knowledge source."""

    PENDING = "pending"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"


class KnowledgeSourceSchema(BaseSchema):
    """Full knowledge source response schema."""

    id: uuid.UUID = Field(description="Unique identifier")
    user_id: str = Field(description="Owner user ID")
    source_type: KnowledgeSourceType = Field(description="Type of knowledge source")
    name: str = Field(description="User-friendly display name")
    file_path: str | None = Field(default=None, description="Local filesystem path")
    status: KnowledgeSourceStatus = Field(description="Connection status")
    last_synced_at: datetime | None = Field(default=None, description="Last sync time")
    error_message: str | None = Field(default=None, description="Error details if any")
    config: dict[str, Any] | None = Field(default=None, description="Source-specific config")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class KnowledgeSourceCreateSchema(BaseSchema):
    """Schema for creating a knowledge source."""

    source_type: KnowledgeSourceType = Field(description="Type of knowledge source")
    name: str = Field(description="User-friendly display name")
    file_path: str | None = Field(default=None, description="Local filesystem path")


class KnowledgeSourceUpdateSchema(BaseSchema):
    """Schema for updating a knowledge source."""

    name: str | None = Field(default=None, description="User-friendly display name")
    file_path: str | None = Field(default=None, description="Local filesystem path")


class KnowledgeSourceListResponse(BaseSchema):
    """Response schema for listing knowledge sources."""

    sources: list[KnowledgeSourceSchema] = Field(description="List of knowledge sources")

"""Pydantic schemas for documents."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from .base import BaseSchema


class DocumentStatus(StrEnum):
    """Status of a document in the indexing pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"
    DELETED = "deleted"


class DocumentSchema(BaseSchema):
    """Full document response schema."""

    id: uuid.UUID = Field(description="Unique identifier")
    knowledge_source_id: uuid.UUID = Field(description="Parent knowledge source ID")
    relative_path: str = Field(description="Path relative to source root")
    title: str | None = Field(default=None, description="Extracted document title")
    content_hash: str = Field(description="SHA-256 hash for change detection")
    file_modified_at: datetime | None = Field(default=None, description="Filesystem mtime")
    status: DocumentStatus = Field(description="Indexing status")
    error_message: str | None = Field(default=None, description="Error details if failed")
    chunk_count: int = Field(description="Number of chunks created")
    doc_metadata: dict[str, Any] | None = Field(default=None, description="Frontmatter, tags, links")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    indexed_at: datetime | None = Field(default=None, description="When embedding completed")


class DocumentCreateSchema(BaseSchema):
    """Schema for creating a document."""

    knowledge_source_id: uuid.UUID = Field(description="Parent knowledge source ID")
    relative_path: str = Field(description="Path relative to source root")
    title: str | None = Field(default=None, description="Extracted document title")
    content_hash: str = Field(description="SHA-256 hash for change detection")
    file_modified_at: datetime | None = Field(default=None, description="Filesystem mtime")
    doc_metadata: dict[str, Any] | None = Field(default=None, description="Frontmatter, tags, links")


class DocumentUpdateSchema(BaseSchema):
    """Schema for updating a document."""

    title: str | None = Field(default=None, description="Extracted document title")
    content_hash: str | None = Field(default=None, description="SHA-256 hash for change detection")
    file_modified_at: datetime | None = Field(default=None, description="Filesystem mtime")
    status: DocumentStatus | None = Field(default=None, description="Indexing status")
    error_message: str | None = Field(default=None, description="Error details if failed")
    chunk_count: int | None = Field(default=None, description="Number of chunks created")
    doc_metadata: dict[str, Any] | None = Field(default=None, description="Frontmatter, tags, links")
    indexed_at: datetime | None = Field(default=None, description="When embedding completed")


class ChunkMetadata(BaseSchema):
    """Structure for chunk metadata JSONB field."""

    headers: list[str] = Field(default_factory=list, description="Markdown header hierarchy")
    start_char: int = Field(description="Character offset start")
    end_char: int = Field(description="Character offset end")
    tags: list[str] = Field(default_factory=list, description="Obsidian-style tags")
    links: list[str] = Field(default_factory=list, description="Wiki-style links")


class DocumentListResponse(BaseSchema):
    """Response schema for listing documents."""

    documents: list[DocumentSchema] = Field(description="List of documents")


class BatchIngestFailure(BaseSchema):
    """Details about a single file that failed to ingest."""

    relative_path: str = Field(description="Path relative to source root")
    error: str = Field(description="Error message")


class BatchIngestResult(BaseSchema):
    """Result of a batch ingestion operation."""

    total_files_found: int = Field(description="Total .md files discovered")
    documents_created: int = Field(description="New documents successfully ingested")
    documents_skipped: int = Field(description="Already indexed, skipped")
    documents_failed: int = Field(description="Failed to ingest")
    failed_files: list[BatchIngestFailure] = Field(default_factory=list)
    duration_seconds: float = Field(description="Total processing time")

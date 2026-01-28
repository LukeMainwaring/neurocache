"""Pydantic schemas for document chunks."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, computed_field

from .base import BaseSchema


class DocumentChunkSchema(BaseSchema):
    """Full document chunk response schema."""

    id: int = Field(description="Unique identifier")
    document_id: uuid.UUID = Field(description="Parent document ID")
    content: str = Field(description="The actual text content")
    chunk_index: int = Field(description="Position in document (0-based)")
    chunk_metadata: dict[str, Any] | None = Field(default=None, description="Headers, offsets, tags")
    token_count: int | None = Field(default=None, description="Token count for context budgeting")
    created_at: datetime = Field(description="Creation timestamp")


class DocumentChunkCreateSchema(BaseSchema):
    """Schema for creating a document chunk."""

    document_id: uuid.UUID = Field(description="Parent document ID")
    content: str = Field(description="The actual text content")
    chunk_index: int = Field(description="Position in document (0-based)")
    embedding: list[float] | None = Field(default=None, description="Vector embedding")
    chunk_metadata: dict[str, Any] | None = Field(default=None, description="Headers, offsets, tags")
    token_count: int | None = Field(default=None, description="Token count for context budgeting")


class DocumentChunkListResponse(BaseSchema):
    """Response schema for listing document chunks."""

    chunks: list[DocumentChunkSchema] = Field(description="List of document chunks")


class ChunkData(BaseSchema):
    """A chunk of text with its associated section metadata."""

    content: str = Field(description="The actual text content")
    section_header: str | None = Field(default=None, description="The header of the section")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def chunk_metadata(self) -> dict[str, str] | None:
        return {"section_header": self.section_header} if self.section_header else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def token_count(self) -> int:
        return len(self.content) // 4

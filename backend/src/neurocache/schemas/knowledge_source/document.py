"""Pydantic schemas for documents."""

import uuid
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field

from ..base import BaseSchema


class DocumentStatus(StrEnum):
    """Status of a document in the indexing pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"
    DELETED = "deleted"


class ContentType(StrEnum):
    """Type of content for tiered knowledge retrieval."""

    PERSONAL_NOTE = "personal_note"
    BOOK_NOTE = "book_note"
    BOOK_SOURCE = "book_source"
    ARTICLE = "article"
    CHAT_INSIGHT = "chat_insight"


class DocumentSchema(BaseSchema):
    """Full document response schema."""

    id: uuid.UUID = Field(description="Unique identifier")
    knowledge_source_id: uuid.UUID = Field(description="Parent knowledge source ID")
    relative_path: str = Field(description="Path relative to source root")
    title: str | None = Field(default=None, description="Extracted document title")
    content_type: ContentType = Field(
        default=ContentType.PERSONAL_NOTE, description="Content type for tiered retrieval"
    )
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
    content_type: ContentType = Field(
        default=ContentType.PERSONAL_NOTE, description="Content type for tiered retrieval"
    )
    content_hash: str = Field(description="SHA-256 hash for change detection")
    file_modified_at: datetime | None = Field(default=None, description="Filesystem mtime")
    doc_metadata: dict[str, Any] | None = Field(default=None, description="Frontmatter, tags, links")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, description="Indexing status")


class DocumentUpdateSchema(BaseSchema):
    """Schema for updating a document."""

    title: str | None = Field(default=None, description="Extracted document title")
    content_type: ContentType | None = Field(default=None, description="Content type for tiered retrieval")
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
    documents_updated: int = Field(description="Modified documents re-ingested")
    documents_deleted: int = Field(description="Removed documents cleaned up")
    documents_skipped: int = Field(description="Unchanged, skipped")
    documents_failed: int = Field(description="Failed to ingest")
    failed_files: list[BatchIngestFailure] = Field(default_factory=list)
    duration_seconds: float = Field(description="Total processing time")


# Top-level directory containing book PDFs and notes
BOOKS_DIR = "Books"


class BookDocumentSummary(BaseSchema):
    """Summary of a single document within a book (note or PDF)."""

    id: uuid.UUID = Field(description="Document ID")
    content_type: ContentType = Field(description="book_note or book_source")
    status: DocumentStatus = Field(description="Indexing status")
    chunk_count: int = Field(description="Number of chunks indexed")
    error_message: str | None = Field(default=None, description="Error details if failed")


class BookSchema(BaseSchema):
    """A book grouped from its Books/ subfolder documents."""

    folder_path: str = Field(description="Relative subfolder path, e.g. 'Books/AI Engineering'")
    title: str = Field(description="Book title from frontmatter or folder name")
    author: str | None = Field(default=None, description="Author from notes frontmatter")
    tags: str | None = Field(default=None, description="Comma-separated tags from frontmatter")
    documents: list[BookDocumentSummary] = Field(description="Component documents (note + PDF)")

    @staticmethod
    def folder_from_path(relative_path: str) -> str | None:
        """Extract book subfolder from a document's relative path.

        For "Books/AI Engineering/notes.md", returns "Books/AI Engineering".
        """
        parts = Path(relative_path).parts
        if len(parts) >= 3 and parts[0] == BOOKS_DIR:
            return f"{BOOKS_DIR}/{parts[1]}"
        return None


class BookListResponse(BaseSchema):
    """Response for listing books from a knowledge source."""

    books: list[BookSchema] = Field(description="Books grouped by subfolder")


class BookPdfPreview(BaseSchema):
    """Parsed metadata from a PDF before upload confirmation."""

    title: str = Field(description="Title from PDF metadata or filename")
    author: str | None = Field(default=None, description="Author from PDF metadata")
    page_count: int = Field(description="Number of pages in the PDF")
    filename: str = Field(description="Original filename")


class BookUploadResponse(BaseSchema):
    """Response after uploading and saving a PDF book."""

    relative_path: str = Field(description="Vault-relative path where the PDF was saved")
    notes_created: bool = Field(description="Whether a Notes.md scaffold was created")

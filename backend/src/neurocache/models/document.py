"""SQLAlchemy model for Document."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neurocache.models.base import Base
from neurocache.schemas.knowledge_source.document import (
    ContentType,
    DocumentCreateSchema,
    DocumentStatus,
    DocumentUpdateSchema,
)

if TYPE_CHECKING:
    from neurocache.models.document_chunk import DocumentChunk


class NoDocumentFound(HTTPException):
    """Exception raised when a document is not found."""

    def __init__(self, detail: str = "Document not found"):
        super().__init__(status_code=404, detail=detail)


class Document(Base):
    """Document model representing an individual file from a KnowledgeSource."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    knowledge_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"), index=True
    )
    relative_path: Mapped[str]
    title: Mapped[str | None]
    content_type: Mapped[str] = mapped_column(default=ContentType.PERSONAL_NOTE)
    content_hash: Mapped[str]
    file_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(default=DocumentStatus.PENDING)
    error_message: Mapped[str | None]
    chunk_count: Mapped[int] = mapped_column(default=0)
    doc_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    chunks: Mapped[list[DocumentChunk]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("knowledge_source_id", "relative_path", name="uq_source_path"),
        Index("ix_documents_knowledge_source_id", "knowledge_source_id"),
        Index("ix_documents_status", "status"),
    )

    @classmethod
    async def get_all_by_source(
        cls,
        db: AsyncSession,
        knowledge_source_id: uuid.UUID,
    ) -> list[Document]:
        """Get all documents for a knowledge source.

        Args:
            db: Database session
            knowledge_source_id: The knowledge source ID

        Returns:
            List of all documents for this source
        """
        result = await db.execute(select(Document).where(Document.knowledge_source_id == knowledge_source_id))
        return list(result.scalars().all())

    @classmethod
    async def get_by_relative_path(
        cls,
        db: AsyncSession,
        knowledge_source_id: uuid.UUID,
        relative_path: str,
    ) -> Document | None:
        """Get a document by its knowledge source ID and relative path.

        Args:
            db: Database session
            knowledge_source_id: The knowledge source ID
            relative_path: Path relative to source root

        Returns:
            Document if exists, None otherwise
        """
        result = await db.execute(
            select(Document).where(
                Document.knowledge_source_id == knowledge_source_id,
                Document.relative_path == relative_path,
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        document_create: DocumentCreateSchema,
    ) -> Document:
        """Create a new document.

        Args:
            db: Database session
            document_create: Document creation schema

        Returns:
            The created Document instance
        """
        document = cls(
            **document_create.model_dump(),
        )
        db.add(document)
        await db.flush()
        await db.refresh(document)
        return document

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        id: uuid.UUID,
        document_update: DocumentUpdateSchema,
    ) -> Document:
        """Update a document.

        Args:
            db: Database session
            id: Document ID
            document_update: Document update schema

        Returns:
            The updated Document instance
        """
        document = await db.get(cls, id)
        if document is None:
            raise NoDocumentFound(f"Document with id {id} not found")
        for field, value in document_update.model_dump(exclude_unset=True).items():
            setattr(document, field, value)
        await db.flush()
        await db.refresh(document)
        return document

    @classmethod
    async def delete(cls, db: AsyncSession, id: uuid.UUID) -> None:
        """Delete a document."""
        document = await db.get(cls, id)
        if document is None:
            raise NoDocumentFound(f"Document with id {id} not found")
        await db.delete(document)
        await db.flush()

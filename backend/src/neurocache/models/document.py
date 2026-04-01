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
    def __init__(self, detail: str = "Document not found"):
        super().__init__(status_code=404, detail=detail)


class Document(Base):
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
        result = await db.execute(select(Document).where(Document.knowledge_source_id == knowledge_source_id))
        return list(result.scalars().all())

    @classmethod
    async def get_books_by_source(
        cls,
        db: AsyncSession,
        knowledge_source_id: uuid.UUID,
    ) -> list[Document]:
        """Returns BOOK_NOTE and BOOK_SOURCE documents, ordered by relative_path for subfolder grouping."""
        result = await db.execute(
            select(Document)
            .where(
                Document.knowledge_source_id == knowledge_source_id,
                Document.content_type.in_([ContentType.BOOK_NOTE, ContentType.BOOK_SOURCE]),
            )
            .order_by(Document.relative_path)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_relative_path(
        cls,
        db: AsyncSession,
        knowledge_source_id: uuid.UUID,
        relative_path: str,
    ) -> Document | None:
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
        document = await db.get(cls, id)
        if document is None:
            raise NoDocumentFound(f"Document with id {id} not found")
        await db.delete(document)
        await db.flush()

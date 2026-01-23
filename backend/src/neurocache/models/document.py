"""SQLAlchemy model for Document."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neurocache.models.base import Base
from neurocache.schemas.document import DocumentStatus

if TYPE_CHECKING:
    from neurocache.models.document_chunk import DocumentChunk


class Document(Base):
    """Document model representing an individual file from a KnowledgeSource."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    knowledge_source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id", ondelete="CASCADE"), index=True)
    relative_path: Mapped[str]
    title: Mapped[str | None]
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

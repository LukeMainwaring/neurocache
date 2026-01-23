"""SQLAlchemy model for DocumentChunk."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neurocache.models.base import Base

if TYPE_CHECKING:
    from neurocache.models.document import Document

# OpenAI text-embedding-3-large with reduced dimensions for HNSW compatibility
EMBEDDING_DIMENSION = 1536


class DocumentChunk(Base):
    """DocumentChunk model storing chunked content with vector embeddings."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    content: Mapped[str]
    chunk_index: Mapped[int]
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSION))
    chunk_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    token_count: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    document: Mapped[Document] = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_document_id", "document_id"),
        # HNSW index for vector similarity search
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

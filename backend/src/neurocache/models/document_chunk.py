"""SQLAlchemy model for DocumentChunk."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from neurocache.core.config import get_settings
from neurocache.models.base import Base
from neurocache.models.knowledge_source import KnowledgeSource

if TYPE_CHECKING:
    from neurocache.models.document import Document

config = get_settings()


class DocumentChunk(Base):
    """DocumentChunk model storing chunked content with vector embeddings."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    content: Mapped[str]
    chunk_index: Mapped[int]
    embedding: Mapped[list[float] | None] = mapped_column(Vector(config.EMBEDDING_DIMENSION))
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

    @classmethod
    async def search_similar(
        cls,
        db: AsyncSession,
        query_embedding: list[float],
        top_k: int = 5,
        knowledge_source_id: str | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for chunks most similar to the query embedding.

        Args:
            db: Database session
            query_embedding: The embedding vector to search for
            top_k: Number of results to return
            knowledge_source_id: Optional filter to search within a specific knowledge source

        Returns:
            List of (DocumentChunk, similarity_score) tuples, ordered by similarity descending.
        """
        distance = cls.embedding.cosine_distance(query_embedding)
        stmt = (
            select(cls, (1 - distance).label("similarity"))
            .where(cls.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        )

        if knowledge_source_id:
            from neurocache.models.document import Document

            stmt = stmt.join(Document).where(Document.knowledge_source_id == knowledge_source_id)

        result = await db.execute(stmt)
        return [(row.DocumentChunk, row.similarity) for row in result.all()]

    @classmethod
    async def search_similar_for_user(
        cls,
        db: AsyncSession,
        query_embedding: list[float],
        user_id: str,
        top_k: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for chunks within all of a user's knowledge sources.

        Args:
            db: Database session
            query_embedding: The embedding vector to search for
            user_id: Filter to chunks from this user's knowledge sources
            top_k: Number of results to return

        Returns:
            List of (DocumentChunk, similarity_score) tuples, ordered by similarity descending.
        """
        from neurocache.models.document import Document

        distance = cls.embedding.cosine_distance(query_embedding)

        stmt = (
            select(cls, (1 - distance).label("similarity"))
            .join(Document)
            .join(KnowledgeSource)
            .where(KnowledgeSource.user_id == user_id)
            .where(cls.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        )

        result = await db.execute(stmt)
        return [(row.DocumentChunk, row.similarity) for row in result.all()]

    @classmethod
    async def get_with_context(
        cls,
        db: AsyncSession,
        chunk_id: int,
    ) -> DocumentChunk | None:
        """Get a chunk with its document eagerly loaded for context.

        Args:
            db: Database session
            chunk_id: The chunk ID to retrieve

        Returns:
            DocumentChunk with document loaded, or None if not found
        """
        stmt = select(cls).where(cls.id == chunk_id).options(selectinload(cls.document))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

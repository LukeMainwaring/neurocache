"""SQLAlchemy model for DocumentChunk."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, func, select
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
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
    search_vector: Mapped[Any | None] = mapped_column(TSVECTOR)
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
        # GIN index for full-text keyword search
        Index("ix_document_chunks_search_vector", "search_vector", postgresql_using="gin"),
    )

    @classmethod
    async def search_similar_for_user(
        cls,
        db: AsyncSession,
        query_embedding: list[float],
        user_id: str,
        top_k: int,
        similarity_threshold: float,
        content_types: list[str] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for chunks within all of a user's knowledge sources.

        Args:
            db: Database session
            query_embedding: The embedding vector to search for
            user_id: Filter to chunks from this user's knowledge sources
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1) to include
            content_types: Optional list of content types to filter by

        Returns:
            List of (DocumentChunk, similarity_score) tuples, ordered by similarity descending.
        """
        from neurocache.models.document import Document

        distance = cls.embedding.cosine_distance(query_embedding)
        similarity = (1 - distance).label("similarity")
        stmt = (
            select(cls, similarity)
            .join(Document)
            .join(KnowledgeSource)
            .where(KnowledgeSource.user_id == user_id)
            .where(cls.embedding.is_not(None))
            .where(1 - distance >= similarity_threshold)
        )
        if content_types:
            stmt = stmt.where(Document.content_type.in_(content_types))
        stmt = stmt.order_by(distance).limit(top_k)
        result = await db.execute(stmt)
        return [(row.DocumentChunk, row.similarity) for row in result.all()]

    @classmethod
    async def search_keyword_for_user(
        cls,
        db: AsyncSession,
        query: str,
        user_id: str,
        top_k: int,
        content_types: list[str] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for chunks using full-text keyword search.

        Uses dual tsquery (english + simple) to match both stemmed content
        and exact metadata terms (tags). Results are scored using cover
        density ranking (ts_rank_cd) which rewards proximity of matching terms.

        Args:
            db: Database session
            query: The search query text
            user_id: Filter to chunks from this user's knowledge sources
            top_k: Maximum number of results to return
            content_types: Optional list of content types to filter by

        Returns:
            List of (DocumentChunk, rank_score) tuples, ordered by rank descending.
        """
        from neurocache.models.document import Document

        # Combine english (stemmed) and simple (exact) tsqueries with OR
        # so that stemmed terms match content and exact terms match tags
        english_query = func.websearch_to_tsquery("english", query)
        simple_query = func.websearch_to_tsquery("simple", query)
        combined_query = english_query.op("||")(simple_query)

        rank = func.ts_rank_cd(cls.search_vector, combined_query).label("rank")
        stmt = (
            select(cls, rank)
            .join(Document)
            .join(KnowledgeSource)
            .where(KnowledgeSource.user_id == user_id)
            .where(cls.search_vector.is_not(None))
            .where(cls.search_vector.op("@@")(combined_query))
        )
        if content_types:
            stmt = stmt.where(Document.content_type.in_(content_types))
        stmt = stmt.order_by(rank.desc()).limit(top_k)
        result = await db.execute(stmt)
        return [(row.DocumentChunk, row.rank) for row in result.all()]

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

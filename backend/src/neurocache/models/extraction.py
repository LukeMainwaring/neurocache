"""SQLAlchemy model for Extraction (conversation-to-knowledge provenance tracking)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Row, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from neurocache.models.base import Base
from neurocache.models.document import Document


class Extraction(Base):
    __tablename__ = "extractions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["thread_id", "agent_type"],
            ["threads.thread_id", "threads.agent_type"],
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[str]
    agent_type: Mapped[str]
    knowledge_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_sources.id"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"))
    status: Mapped[str] = mapped_column(default="completed")
    error_message: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @classmethod
    async def get_by_thread(
        cls,
        db: AsyncSession,
        thread_id: str,
        agent_type: str,
    ) -> list[Extraction]:
        """Get all extractions for a thread."""
        result = await db.execute(
            select(cls).where(cls.thread_id == thread_id, cls.agent_type == agent_type).order_by(cls.created_at.desc())
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_thread_with_paths(
        cls,
        db: AsyncSession,
        thread_id: str,
        agent_type: str,
    ) -> list[Row[tuple[Extraction, str]]]:
        """Get all extractions for a thread with document relative paths.

        Returns:
            List of (Extraction, relative_path) rows, ordered by most recent first.
        """
        result = await db.execute(
            select(cls, Document.relative_path)
            .join(Document, cls.document_id == Document.id)
            .where(cls.thread_id == thread_id, cls.agent_type == agent_type)
            .order_by(cls.created_at.desc())
        )
        return list(result.all())

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        *,
        thread_id: str,
        agent_type: str,
        knowledge_source_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Extraction:
        """Create a new extraction record."""
        extraction = cls(
            thread_id=thread_id,
            agent_type=agent_type,
            knowledge_source_id=knowledge_source_id,
            document_id=document_id,
        )
        db.add(extraction)
        await db.flush()
        return extraction

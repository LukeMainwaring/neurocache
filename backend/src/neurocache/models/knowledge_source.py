"""SQLAlchemy model for KnowledgeSource."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from neurocache.models.base import Base
from neurocache.schemas.knowledge_source import (
    KnowledgeSourceCreateSchema,
    KnowledgeSourceSchema,
    KnowledgeSourceStatus,
    KnowledgeSourceUpdateSchema,
)


class NoKnowledgeSourceFound(HTTPException):
    """Exception raised when a knowledge source is not found."""

    def __init__(self, detail: str = "Knowledge source not found"):
        super().__init__(status_code=404, detail=detail)


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    source_type: Mapped[str]
    name: Mapped[str]
    file_path: Mapped[str | None]
    status: Mapped[str] = mapped_column(default=KnowledgeSourceStatus.PENDING)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None]
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("user_id", "source_type", "file_path", name="uq_user_source_path"),
        Index("ix_knowledge_sources_user_id", "user_id"),
    )

    @classmethod
    async def get(cls, db: AsyncSession, id: str, user_id: str) -> KnowledgeSourceSchema:
        """Get a knowledge source by ID for a specific user."""
        source = await db.get(cls, id)
        if source is None or source.user_id != user_id:
            raise NoKnowledgeSourceFound(f"Knowledge source with id {id} not found")
        return KnowledgeSourceSchema.model_validate(source)

    @classmethod
    async def list_for_user(cls, db: AsyncSession, user_id: str) -> list[KnowledgeSourceSchema]:
        """List all knowledge sources for a user."""
        result = await db.execute(select(cls).where(cls.user_id == user_id).order_by(cls.created_at.desc()))
        sources = result.scalars().all()
        return [KnowledgeSourceSchema.model_validate(source) for source in sources]

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        user_id: str,
        source_create: KnowledgeSourceCreateSchema,
    ) -> KnowledgeSourceSchema:
        """Create a new knowledge source."""
        source = cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            **source_create.model_dump(),
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        return KnowledgeSourceSchema.model_validate(source)

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        id: str,
        user_id: str,
        source_update: KnowledgeSourceUpdateSchema,
    ) -> KnowledgeSourceSchema:
        """Update a knowledge source."""
        source = await db.get(cls, id)
        if source is None or source.user_id != user_id:
            raise NoKnowledgeSourceFound(f"Knowledge source with id {id} not found")
        for field, value in source_update.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(source, field, value)
        await db.commit()
        await db.refresh(source)
        return KnowledgeSourceSchema.model_validate(source)

    @classmethod
    async def delete(cls, db: AsyncSession, id: str, user_id: str) -> None:
        """Delete a knowledge source."""
        source = await db.get(cls, id)
        if source is None or source.user_id != user_id:
            raise NoKnowledgeSourceFound(f"Knowledge source with id {id} not found")
        await db.delete(source)
        await db.commit()

    @classmethod
    async def update_status(
        cls,
        db: AsyncSession,
        id: str,
        user_id: str,
        status: str,
        error_message: str | None = None,
    ) -> KnowledgeSourceSchema:
        """Update the status of a knowledge source."""
        source = await db.get(cls, id)
        if source is None or source.user_id != user_id:
            raise NoKnowledgeSourceFound(f"Knowledge source with id {id} not found")
        source.status = status
        source.error_message = error_message
        await db.commit()
        await db.refresh(source)
        return KnowledgeSourceSchema.model_validate(source)

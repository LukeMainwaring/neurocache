from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from neurocache.models.base import Base
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.thread import ThreadCreateSchema, ThreadSchema


class NoThreadFound(HTTPException):
    def __init__(self, detail: str = "Thread not found"):
        super().__init__(status_code=404, detail=detail)


class Thread(Base):
    __tablename__ = "threads"

    thread_id: Mapped[str]
    agent_type: Mapped[str]
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    __table_args__ = (PrimaryKeyConstraint("thread_id", "agent_type"),)

    @classmethod
    async def get(cls, db: AsyncSession, thread_id: str, agent_type: str) -> Thread | None:
        result = await db.execute(select(cls).where(cls.thread_id == thread_id, cls.agent_type == agent_type))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db: AsyncSession, thread_create: ThreadCreateSchema) -> ThreadSchema:
        thread = cls(
            thread_id=thread_create.thread_id,
            agent_type=thread_create.agent_type.value,
            user_id=thread_create.user_id,
        )
        db.add(thread)
        await db.flush()
        await db.refresh(thread)
        return ThreadSchema.model_validate(thread)

    @classmethod
    async def get_or_create(cls, db: AsyncSession, thread_id: str, agent_type: str, user_id: str) -> ThreadSchema:
        thread = await cls.get(db, thread_id, agent_type)
        if thread:
            return ThreadSchema.model_validate(thread)
        return await cls.create(
            db,
            ThreadCreateSchema(
                thread_id=thread_id,
                agent_type=AgentType(agent_type),
                user_id=user_id,
            ),
        )

    @classmethod
    async def list_for_user(cls, db: AsyncSession, user_id: str, agent_type: str) -> list[Thread]:
        result = await db.execute(
            select(cls).where(cls.user_id == user_id, cls.agent_type == agent_type).order_by(cls.updated_at.desc())
        )
        return list(result.scalars().all())

    @classmethod
    async def get_for_user(cls, db: AsyncSession, thread_id: str, user_id: str, agent_type: str) -> Thread:
        result = await db.execute(
            select(cls).where(cls.thread_id == thread_id, cls.user_id == user_id, cls.agent_type == agent_type)
        )
        thread = result.scalar_one_or_none()
        if not thread:
            raise NoThreadFound()
        return thread

    @classmethod
    async def delete_for_user(cls, db: AsyncSession, thread_id: str, user_id: str, agent_type: str) -> None:
        await db.execute(
            delete(cls).where(cls.thread_id == thread_id, cls.user_id == user_id, cls.agent_type == agent_type)
        )
        await db.flush()

    @classmethod
    async def update_title(cls, db: AsyncSession, thread_id: str, agent_type: str, title: str) -> None:
        thread = await cls.get(db, thread_id, agent_type)
        if thread:
            thread.title = title
            await db.flush()

"""SQLAlchemy model for User."""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import DateTime, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from neurocache.models.base import Base
from neurocache.schemas.user import UserCreateSchema, UserPersonalizationUpdateSchema, UserSchema


class NoUserFound(HTTPException):
    """Exception raised when a user is not found."""

    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=404, detail=detail)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(index=True)
    name: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    # Personalization fields
    custom_instructions: Mapped[str | None]
    nickname: Mapped[str | None]
    occupation: Mapped[str | None]
    about_you: Mapped[str | None]

    @classmethod
    async def get(cls, db: AsyncSession, id: str) -> UserSchema:
        """Reads a user by id."""
        user = await db.get(cls, id)
        if user is None:
            raise NoUserFound(f"User with id {id} not found")
        return UserSchema.model_validate(user)

    @classmethod
    async def list_all(cls, db: AsyncSession) -> list[UserSchema]:
        result = await db.execute(select(cls))
        users = result.scalars().all()
        return [UserSchema.model_validate(user) for user in users]

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        user_create_schema: UserCreateSchema,
    ) -> UserSchema:
        user = cls(**user_create_schema.model_dump())
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return UserSchema.model_validate(user)

    @classmethod
    async def update_email(cls, db: AsyncSession, id: str, email: str) -> UserSchema:
        """Update a user's email address."""
        user = await db.get(cls, id)
        if user is None:
            raise NoUserFound(f"User with id {id} not found")
        user.email = email
        await db.flush()
        await db.refresh(user)
        return UserSchema.model_validate(user)

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        id: str,
        user_update: UserSchema,
    ) -> UserSchema:
        user = await db.get(cls, id)
        if user is None:
            raise NoUserFound(f"User with id {id} not found")
        for field, value in user_update.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(user, field, value)
        await db.flush()
        await db.refresh(user)
        return UserSchema.model_validate(user)

    @classmethod
    async def update_personalization(
        cls,
        db: AsyncSession,
        id: str,
        personalization: UserPersonalizationUpdateSchema,
    ) -> UserSchema:
        """Update user personalization settings."""
        user = await db.get(cls, id)
        if user is None:
            raise NoUserFound(f"User with id {id} not found")
        for field, value in personalization.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await db.flush()
        await db.refresh(user)
        return UserSchema.model_validate(user)

    @classmethod
    async def delete(cls, db: AsyncSession, user_id: str) -> None:
        user = await db.get(cls, user_id)
        if user is None:
            raise NoUserFound(f"User with id {user_id} not found")
        await db.delete(user)
        await db.flush()

    @classmethod
    async def exists(cls, db: AsyncSession, id: str) -> bool:
        """Check if a user exists."""
        result = await db.execute(select(exists(cls.id).where(cls.id == id)))
        return result.scalar_one()

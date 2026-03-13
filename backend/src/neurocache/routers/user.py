"""User management API endpoints.

This module provides REST API endpoints for user CRUD operations.
"""

import logging

from fastapi import APIRouter, Depends

from neurocache.dependencies.auth.auth import AuthenticatedUser, get_current_user_email
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.models.user import NoUserFound, User
from neurocache.schemas.user import UserCreateSchema, UserPersonalizationUpdateSchema, UserSchema

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/myself")
async def get_myself(
    user_id: AuthenticatedUser,
    db: AsyncPostgresSessionDep,
    email: str = Depends(get_current_user_email),
) -> UserSchema:
    """Get the current user, auto-creating on first login."""
    try:
        user = await User.get(db, id=user_id)
        if user.email != email:
            logger.warning(f"User email mismatch: {user.email} != {email}. Updating email.")
            user = await User.update_email(db, id=user_id, email=email)
    except NoUserFound:
        user = await User.create(db, UserCreateSchema(id=user_id, email=email, name=email))
    return user


@user_router.patch("/myself/personalization")
async def update_my_personalization(
    user_id: AuthenticatedUser,
    update_data: UserPersonalizationUpdateSchema,
    db: AsyncPostgresSessionDep,
) -> UserSchema:
    """Update the current user's personalization settings."""
    return await User.update_personalization(db, user_id, update_data)


@user_router.get("")
async def list_users(db: AsyncPostgresSessionDep, _user_id: AuthenticatedUser) -> list[UserSchema]:
    """List all users."""
    return await User.list_all(db)

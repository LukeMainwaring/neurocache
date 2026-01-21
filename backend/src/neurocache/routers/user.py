"""User management API endpoints.

This module provides REST API endpoints for user CRUD operations.
"""

import logging

from fastapi import APIRouter

from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.models.user import NoUserFound, User
from neurocache.schemas.user import UserCreateSchema, UserPersonalizationUpdateSchema, UserSchema

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/users", tags=["users"])


DEMO_USER_ID = "110771214372945994893"


@user_router.get("/myself")
async def get_myself(
    db: AsyncPostgresSessionDep,
    # current_user_id: str = Security(get_current_user_id),
    # current_user_email: str = Depends(get_current_user_email),
) -> UserSchema:
    """Get a user by ID."""
    try:
        # user = await User.get(db, id=current_user_id)
        user = await User.get(db, id=DEMO_USER_ID)
    except NoUserFound:
        # user = await User.create(db, UserSchema(id=current_user_id, email=current_user_email, name="Luke Skywalker"))
        user = await User.create(
            db, UserCreateSchema(id=DEMO_USER_ID, email="lfmainwaring@gmail.com", name="Luke Skywalker")
        )
    return user


@user_router.patch("/myself/personalization")
async def update_my_personalization(
    update_data: UserPersonalizationUpdateSchema,
    db: AsyncPostgresSessionDep,
) -> UserSchema:
    """Update the current user's personalization settings."""
    return await User.update_personalization(db, DEMO_USER_ID, update_data)


@user_router.get("")
async def list_users(db: AsyncPostgresSessionDep, _user_id: AuthenticatedUser) -> list[UserSchema]:
    """List all users."""
    return await User.list_all(db)

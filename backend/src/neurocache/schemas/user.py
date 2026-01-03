from datetime import datetime

from pydantic import Field

from .base import BaseSchema


class UserSchema(BaseSchema):
    id: str = Field(description="Unique user identifier")
    email: str = Field(description="User's email")
    name: str = Field(description="User's name")
    created_at: datetime = Field(description="When this user profile was created")
    updated_at: datetime = Field(description="When this user profile was last updated")


class UserCreateSchema(BaseSchema):
    id: str = Field(description="Unique user identifier")
    email: str = Field(description="User's email")
    name: str = Field(description="User's name")

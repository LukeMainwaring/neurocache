from datetime import datetime

from pydantic import Field

from .base import BaseSchema


class UserSchema(BaseSchema):
    id: str = Field(description="Unique user identifier")
    email: str = Field(description="User's email")
    name: str = Field(description="User's name")
    created_at: datetime = Field(description="When this user profile was created")
    updated_at: datetime = Field(description="When this user profile was last updated")

    # Personalization fields
    custom_instructions: str | None = Field(default=None, description="Custom instructions for the AI")
    nickname: str | None = Field(default=None, description="Preferred nickname")
    occupation: str | None = Field(default=None, description="User's occupation")
    about_you: str | None = Field(default=None, description="Information about the user")


class UserCreateSchema(BaseSchema):
    id: str = Field(description="Unique user identifier")
    email: str = Field(description="User's email")
    name: str = Field(description="User's name")


class UserPersonalizationUpdateSchema(BaseSchema):
    """Schema for updating user personalization settings."""

    custom_instructions: str | None = None
    nickname: str | None = None
    occupation: str | None = None
    about_you: str | None = None

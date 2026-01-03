"""Thread schemas for conversation persistence."""

from datetime import datetime

from neurocache.schemas.agent_type import AgentType

from .base import BaseSchema


class ThreadSchema(BaseSchema):
    """Thread schema representing a conversation thread."""

    thread_id: str
    agent_type: AgentType
    user_id: str
    created_at: datetime
    updated_at: datetime


class ThreadCreateSchema(BaseSchema):
    """Schema for creating a new thread."""

    thread_id: str
    agent_type: AgentType
    user_id: str

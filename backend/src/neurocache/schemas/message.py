from enum import StrEnum
from typing import Literal

from pydantic import Field

from .base import BaseSchema


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MessageMetadata(BaseSchema):
    original_llm_response: str | None = None
    should_send: bool | None = None


class ToolCall(BaseSchema):
    tool_call_id: str
    tool_name: str
    arguments: str | None
    result: str | None = None
    error: str | None = None


class MessageBase(BaseSchema):
    thread_id: str
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)


class ToolCallMessage(MessageBase):
    role: Literal[MessageRole.TOOL] = MessageRole.TOOL
    content: ToolCall


class UserMessage(MessageBase):
    role: Literal[MessageRole.USER] = MessageRole.USER
    content: str


class AssistantMessage(MessageBase):
    role: Literal[MessageRole.ASSISTANT] = MessageRole.ASSISTANT
    content: str


AgentMessage = ToolCallMessage | UserMessage | AssistantMessage

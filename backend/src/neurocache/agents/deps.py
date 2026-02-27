"""Shared dependencies for all Pydantic AI agents."""

from dataclasses import dataclass, field

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.schemas.user import UserSchema
from neurocache.utils.message_serialization import RAGSource


@dataclass
class AgentDeps:
    """Dependencies injected into agent runs.

    Mutable ``rag_sources`` accumulates source metadata across tool calls
    within a single turn so the router can persist them after the run.
    """

    user: UserSchema
    db: AsyncSession
    openai_client: AsyncOpenAI
    rag_sources: list[RAGSource] = field(default_factory=list)

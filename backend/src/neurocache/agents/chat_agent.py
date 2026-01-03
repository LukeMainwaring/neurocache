"""Chat agent for general conversational interaction with knowledge base.

This module provides a simple chat agent that:
- Engages in natural conversation with the user
- Has access to the user's personal knowledge base (future: RAG integration)
- Maintains conversation history across sessions
"""

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.agents.shared import (
    get_history,
    update_history,
)
from neurocache.core.config import get_settings
from neurocache.models.user import User as UserModel
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.message import UserMessage
from neurocache.schemas.user import UserSchema

logger = logging.getLogger(__name__)

config = get_settings()

# ============================================================================
# Chat Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are a helpful AI assistant with access to the user's personal knowledge base.

Your role is to:
- Have natural, engaging conversations with the user
- Help them explore ideas and concepts from their knowledge base
- Draw connections across different topics and sources
- Answer questions clearly and concisely

Keep your responses conversational and helpful. When you don't know something, say so directly.""".strip()

# ============================================================================
# Agent Creation and Instructions
# ============================================================================


def build_chat_instructions(ctx: RunContext[UserSchema]) -> str:
    """Build instructions for the chat agent.

    Args:
        ctx: Pydantic AI RunContext containing User data

    Returns:
        Complete chat instructions with user context
    """
    user = ctx.deps

    return f"""{SYSTEM_PROMPT}

---

You are chatting with {user.name} (email: {user.email}).""".strip()


def create_chat_agent() -> Agent[UserSchema, str]:
    """Create chat agent for general conversation.

    Returns:
        Agent configured with User dependencies and chat instructions
    """
    model = OpenAIChatModel(model_name=config.AGENT_MODEL, settings=ModelSettings(temperature=config.AGENT_TEMPERATURE))

    return Agent(
        model=model,
        deps_type=UserSchema,
        instructions=build_chat_instructions,
    )


# ============================================================================
# Streaming Handler
# ============================================================================


async def chat_agent_stream(
    message: UserMessage,
    db: AsyncSession,
    user_id: str,
) -> AsyncGenerator[str, None]:
    """Handle streaming for chat agent.

    Streams response in Vercel AI SDK compatible SSE format with token-by-token streaming.

    Args:
        message: User message containing query and thread_id
        user_id: User ID
        db: Database session

    Yields:
        Server-Sent Events formatted strings compatible with Vercel AI SDK v1 protocol
    """
    thread_id = message.thread_id

    user = await UserModel.get(db, user_id)

    # Get message history from shared manager (namespaced for chat agent)
    original_message_history = await get_history(db, thread_id, AgentType.CHAT)
    original_user_query = message.content

    # Generate unique IDs for this message stream
    message_id = str(uuid.uuid4())
    text_block_id = str(uuid.uuid4())

    try:
        # Send message start event
        yield f"data: {json.dumps({'type': 'start', 'messageId': message_id})}\n\n"

        # Send text start event
        yield f"data: {json.dumps({'type': 'text-start', 'id': text_block_id})}\n\n"

        # Run chat agent with streaming
        agent = create_chat_agent()
        async with agent.run_stream(
            user_prompt=original_user_query,
            message_history=original_message_history,
            deps=user,
        ) as result:
            # Stream text deltas as they arrive
            # delta=True gives us incremental chunks rather than accumulated text
            async for text_chunk in result.stream_text(delta=True):
                # Send each chunk in official SSE format
                yield f"data: {json.dumps({'type': 'text-delta', 'id': text_block_id, 'delta': text_chunk})}\n\n"

        # Send text end event
        yield f"data: {json.dumps({'type': 'text-end', 'id': text_block_id})}\n\n"

        # Send finish event
        yield f"data: {json.dumps({'type': 'finish'})}\n\n"

        # Update message history
        output = await result.get_output()
        if output is not None:
            # Update message history with new messages
            original_message_history.extend(result.new_messages())
            # Update shared history (namespaced for chat agent)
            await update_history(db, thread_id, original_message_history, AgentType.CHAT, user_id)

    except Exception:
        logger.exception("Error in chat agent streaming")
        # Send error in official SSE format
        error_message = "An error occurred while processing your request."
        yield f"data: {json.dumps({'type': 'error', 'errorText': error_message})}\n\n"
        raise

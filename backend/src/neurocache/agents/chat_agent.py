"""Chat agent for general conversational interaction with knowledge base.

This module provides a simple chat agent that:
- Engages in natural conversation with the user
- Has access to the user's personal knowledge base via RAG
- Maintains conversation history across sessions
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.agents.shared import get_history, save_new_messages
from neurocache.core.config import get_settings
from neurocache.models.document_chunk import DocumentChunk
from neurocache.models.thread import Thread
from neurocache.models.user import User as UserModel
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.document import ContentType
from neurocache.schemas.message import UserMessage
from neurocache.schemas.user import UserSchema
from neurocache.services.knowledge_source.retrieval import search_similar_chunks_for_user
from neurocache.services.title_generator import generate_thread_title
from neurocache.utils.message_serialization import RAGSource, prepare_messages_for_storage

logger = logging.getLogger(__name__)

config = get_settings()

# ============================================================================
# Chat Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are the user's personal AI assistant and "second brain"—an extension of their thinking that understands their context, interests, and goals.

Your core traits:
- Thoughtful: Consider the user's background and perspective when responding
- Connective: Draw links between ideas, even across different domains
- Direct: Be concise and honest. Say "I don't know" when appropriate
- Adaptive: Match your tone and depth to what the user needs

When helping the user:
- Build on what you know about them rather than treating each conversation as isolated
- Proactively surface relevant connections when they might be useful
- Ask clarifying questions when the user's intent is ambiguous""".strip()

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

    sections = [SYSTEM_PROMPT]

    # User context section
    user_context = []
    name = user.nickname or user.name
    if name:
        user_context.append(f"You're chatting with {name}.")
    if user.occupation:
        user_context.append(f"They work as a {user.occupation}.")
    if user.about_you:
        user_context.append(f"Background: {user.about_you}")

    if user_context:
        sections.append("## About the User\n" + "\n".join(user_context))

    # Custom instructions get their own prominent section with explicit priority
    if user.custom_instructions:
        sections.append(
            "## User's Custom Instructions\n"
            "Follow these instructions from the user. "
            "They take priority over default behavior:\n\n"
            f"{user.custom_instructions}"
        )

    return "\n\n".join(sections)


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
# RAG Context Retrieval
# ============================================================================


def _content_type_label(content_type: str | None) -> str:
    """Return a human-readable label for a content type."""
    labels: dict[str, str] = {
        ContentType.PERSONAL_NOTE.value: "Personal Note",
        ContentType.BOOK_NOTE.value: "Book Note",
        ContentType.ARTICLE.value: "Article",
    }
    return labels.get(content_type, "Note") if content_type else "Note"


def format_rag_context(
    relevant_chunks: list[tuple[DocumentChunk, float]],
) -> tuple[str | None, list[RAGSource]]:
    """Format retrieved chunks into context for the prompt.

    Reconstructs attribution prefixes from chunk metadata and document path
    (the chunk content itself is stored without prefixes for clean embeddings).
    Includes content type and book-specific metadata (author) when available.

    Args:
        chunks: List of (chunk, similarity) tuples from retrieval

    Returns:
        Tuple of (formatted_context, sources_metadata)
        - formatted_context: String for the prompt, or None if no relevant chunks
        - sources_metadata: List of source info dicts for the frontend
    """
    if not relevant_chunks:
        return None, []

    context_parts = []
    sources: list[RAGSource] = []

    for chunk, similarity in relevant_chunks:
        doc = chunk.document
        source_path = doc.relative_path if doc else "Unknown"
        content_type = doc.content_type if doc else None
        doc_metadata = doc.doc_metadata if doc else None

        # Build attribution prefix with content type
        type_label = _content_type_label(content_type)
        prefix = f"[Source: {source_path} ({type_label})]"

        # Add author for book notes
        if content_type == ContentType.BOOK_NOTE.value and doc_metadata:
            author = doc_metadata.get("author")
            if author:
                prefix += f"\n[Author: {author}]"

        # Add section header if available
        section_header = (chunk.chunk_metadata or {}).get("section_header")
        if section_header:
            prefix += f"\n[Section: {section_header}]"

        context_parts.append(f"{prefix}\n\n{chunk.content}")

        # Build source metadata for frontend
        source: RAGSource = {
            "path": source_path,
            "similarity": float(similarity),
            "content": chunk.content,
        }
        if content_type:
            source["content_type"] = content_type
        if section_header:
            source["section_header"] = section_header
        if content_type == ContentType.BOOK_NOTE.value and doc_metadata:
            if doc_metadata.get("author"):
                source["author"] = doc_metadata["author"]
        sources.append(source)

    return "\n\n---\n\n".join(context_parts), sources


async def retrieve_context(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    query: str,
    user_id: str,
) -> tuple[str | None, list[RAGSource]]:
    """Retrieve relevant context from the user's knowledge base.

    Args:
        db: Database session
        openai_client: OpenAI client for embeddings
        query: The user's query
        user_id: User ID to scope the search

    Returns:
        Tuple of (formatted_context, sources_metadata)
    """
    try:
        # Document relationships are loaded by search_similar_chunks_for_user
        # during content-type boosting
        relevant_chunks = await search_similar_chunks_for_user(db, openai_client, query, user_id)
        if not relevant_chunks:
            return None, []
        return format_rag_context(relevant_chunks)
    except Exception:
        logger.exception("Error retrieving RAG context")
        return None, []


# ============================================================================
# Streaming Handler
# ============================================================================


async def chat_agent_stream(
    message: UserMessage,
    db: AsyncSession,
    user_id: str,
    openai_client: AsyncOpenAI,
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

    # Retrieve relevant context from knowledge base
    rag_context, rag_sources = await retrieve_context(db, openai_client, original_user_query, user_id)
    # Augment user prompt with context if available
    if rag_context:
        augmented_prompt = f"{original_user_query}\n\n---\nRelevant information from your notes:\n\n{rag_context}"
        logger.info("RAG: Augmented prompt with context: %s", augmented_prompt)
    else:
        augmented_prompt = original_user_query
        logger.info("RAG: No relevant context found")

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
            user_prompt=augmented_prompt,
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
            new_messages = prepare_messages_for_storage(
                result.new_messages(),
                original_user_query,
                rag_sources,
            )
            await save_new_messages(db, thread_id, AgentType.CHAT, user_id, new_messages)

            # Generate title for new threads (first exchange)
            thread = await Thread.get(db, thread_id, AgentType.CHAT.value)
            if thread and thread.title is None:
                asyncio.create_task(
                    generate_thread_title(
                        thread_id=thread_id,
                        agent_type=AgentType.CHAT.value,
                        user_message=original_user_query,
                        assistant_response=output,
                    )
                )

    except Exception:
        logger.exception("Error in chat agent streaming")
        # Send error in official SSE format
        error_message = "An error occurred while processing your request."
        yield f"data: {json.dumps({'type': 'error', 'errorText': error_message})}\n\n"
        raise

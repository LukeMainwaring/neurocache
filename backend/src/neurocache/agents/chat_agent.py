"""Chat agent for general conversational interaction with knowledge base.

This module provides a simple chat agent that:
- Engages in natural conversation with the user
- Has access to the user's personal knowledge base via RAG
- Maintains conversation history across sessions
"""

import logging

import logfire
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.core.config import get_settings
from neurocache.models.document_chunk import DocumentChunk
from neurocache.schemas.knowledge_source.document import ContentType
from neurocache.schemas.user import UserSchema
from neurocache.services.knowledge_source.retrieval import search_similar_chunks_for_user
from neurocache.utils.message_serialization import RAGSource

logfire.configure()
logfire.instrument_pydantic_ai()

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


_model = OpenAIChatModel(model_name=config.AGENT_MODEL, settings=ModelSettings(temperature=config.AGENT_TEMPERATURE))

chat_agent = Agent(
    model=_model,
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
        ContentType.BOOK_SOURCE.value: "Book Source",
        ContentType.ARTICLE.value: "Article",
    }
    return labels.get(content_type, "Note") if content_type else "Note"


def format_rag_context(
    relevant_chunks: list[tuple[DocumentChunk, float]],
) -> tuple[str | None, list[RAGSource]]:
    """Format retrieved chunks into context for the prompt.

    Reconstructs attribution prefixes from chunk metadata and document path
    (the chunk content itself is stored without prefixes for clean embeddings).
    Includes content type, book-specific metadata (author), and PDF metadata
    (page number, chapter) when available.

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
        chunk_meta = chunk.chunk_metadata or {}

        # Build attribution prefix with content type
        type_label = _content_type_label(content_type)
        prefix = f"[Source: {source_path} ({type_label})]"

        # Add author for book notes and book sources
        if content_type in (ContentType.BOOK_NOTE.value, ContentType.BOOK_SOURCE.value) and doc_metadata:
            author = doc_metadata.get("author")
            if author:
                prefix += f"\n[Author: {author}]"

        # Add page number for book sources (PDFs)
        page_number = chunk_meta.get("page_number")
        if page_number:
            prefix += f"\n[Page: {page_number}]"

        # Add chapter for book sources (PDFs)
        chapter = chunk_meta.get("chapter")
        if chapter:
            prefix += f"\n[Chapter: {chapter}]"

        # Add section header if available (markdown documents)
        section_header = chunk_meta.get("section_header")
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
        if page_number:
            source["page_number"] = page_number
        if chapter:
            source["chapter"] = chapter
        if content_type in (ContentType.BOOK_NOTE.value, ContentType.BOOK_SOURCE.value) and doc_metadata:
            if doc_metadata.get("author"):
                source["author"] = doc_metadata["author"]
        sources.append(source)

    return "\n\n---\n\n".join(context_parts), sources


def format_rag_instructions(rag_context: str) -> str:
    """Format RAG context as runtime instructions for the agent.

    Args:
        rag_context: Formatted context string from format_rag_context()

    Returns:
        Instructions string to pass as runtime instructions to the adapter
    """
    return (
        "## Retrieved Context\n"
        "The following information was retrieved from the user's knowledge base "
        "as potentially relevant to their current message:\n\n"
        f"{rag_context}"
    )


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

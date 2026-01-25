"""Retrieval service for semantic search over document chunks."""

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.document_chunk import DocumentChunk
from neurocache.services.embedding import generate_embedding

logger = logging.getLogger(__name__)

# TODO: decide if there should be a similarity threshold. if so, what should it be?
DEFAULT_TOP_K = 5


async def search_similar_chunks(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    knowledge_source_id: uuid.UUID | None = None,
) -> list[tuple[DocumentChunk, float]]:
    """Search for document chunks most similar to the query.

    Args:
        db: Database session
        openai_client: OpenAI client for generating query embedding
        query: The search query text
        top_k: Number of results to return (default 5)
        knowledge_source_id: Optional filter to search within a specific knowledge source

    Returns:
        List of (DocumentChunk, similarity_score) tuples, ordered by similarity descending.
    """
    query_embedding = await generate_embedding(openai_client, query)
    return await DocumentChunk.search_similar(db, query_embedding, top_k, knowledge_source_id)


async def search_similar_chunks_for_user(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    query: str,
    user_id: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[tuple[DocumentChunk, float]]:
    """Search for document chunks within all of a user's knowledge sources.

    Args:
        db: Database session
        openai_client: OpenAI client for generating query embedding
        query: The search query text
        user_id: Filter to chunks from this user's knowledge sources
        top_k: Number of results to return (default 5)

    Returns:
        List of (DocumentChunk, similarity_score) tuples, ordered by similarity descending.
    """
    query_embedding = await generate_embedding(openai_client, query)
    return await DocumentChunk.search_similar_for_user(db, query_embedding, user_id, top_k)


async def get_chunk_with_context(
    db: AsyncSession,
    chunk_id: int,
) -> dict[str, str | None]:
    """Get a chunk along with its document context for citation.

    Args:
        db: Database session
        chunk_id: The chunk ID to retrieve

    Returns:
        Dict with chunk content and document metadata for citation
    """
    chunk = await DocumentChunk.get_with_context(db, chunk_id)

    if not chunk:
        return {"content": None, "title": None, "path": None}

    return {
        "content": chunk.content,
        "title": chunk.document.title,
        "path": chunk.document.relative_path,
    }

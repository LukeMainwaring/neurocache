"""Retrieval service for semantic search over document chunks."""

import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.document_chunk import DocumentChunk
from neurocache.schemas.knowledge_source.document import ContentType
from neurocache.services.embedding import generate_embedding

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 10
RAG_SIMILARITY_THRESHOLD = 0.3  # Minimum similarity to include in the RAG context

# Three-tier content type boosting for retrieval ranking.
# Personal notes rank highest, then user's book notes, then raw book sources.
CONTENT_TYPE_BOOSTS: dict[str, float] = {
    ContentType.PERSONAL_NOTE.value: 1.04,  # 4% boost - user's own thoughts
    ContentType.BOOK_NOTE.value: 1.02,  # 2% boost - user's book summaries
    ContentType.ARTICLE.value: 1.01,  # 1% boost - curated articles
    ContentType.BOOK_SOURCE.value: 1.00,  # baseline - raw PDF content
}


def apply_content_type_boost(
    chunks: list[tuple[DocumentChunk, float]],
) -> list[tuple[DocumentChunk, float]]:
    """Apply content-type-aware boosting to similarity scores.

    Uses three-tier boosting:
    - Personal notes: 4% boost (user's own thoughts rank highest)
    - Book notes: 2% boost (user's summaries of books)
    - Articles: 1% boost (curated content)
    - Book sources: baseline (raw PDF content as supporting evidence)

    Args:
        chunks: List of (chunk, similarity) tuples with documents loaded

    Returns:
        Re-sorted list with adjusted scores
    """
    boosted: list[tuple[DocumentChunk, float]] = []
    for chunk, similarity in chunks:
        content_type = chunk.document.content_type if chunk.document else None
        boost = CONTENT_TYPE_BOOSTS.get(content_type, 1.0) if content_type else 1.0
        # Apply boost, cap at 1.0
        adjusted = min(similarity * boost, 1.0)
        boosted.append((chunk, adjusted))

    # Re-sort by adjusted similarity
    boosted.sort(key=lambda x: x[1], reverse=True)
    return boosted


async def search_similar_chunks_for_user(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    query: str,
    user_id: str,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = RAG_SIMILARITY_THRESHOLD,
    content_types: list[ContentType] | None = None,
    apply_boost: bool = True,
) -> list[tuple[DocumentChunk, float]]:
    """Search for document chunks within all of a user's knowledge sources.

    Args:
        db: Database session
        openai_client: OpenAI client for generating query embedding
        query: The search query text
        user_id: Filter to chunks from this user's knowledge sources
        top_k: Maximum number of results to return
        similarity_threshold: Minimum similarity score to include in the results
        content_types: Optional list of content types to filter by
        apply_boost: Whether to apply content-type-aware score boosting

    Returns:
        List of (DocumentChunk, similarity_score) tuples, ordered by similarity descending.
    """
    query_embedding = await generate_embedding(openai_client, query)

    # Convert enum to string values for DB query
    type_values = [ct.value for ct in content_types] if content_types else None

    chunks = await DocumentChunk.search_similar_for_user(
        db, query_embedding, user_id, top_k, similarity_threshold, type_values
    )

    # Apply content-type boosting if enabled and we have results
    if apply_boost and chunks:
        # Load document relationships for boosting logic
        for chunk, _ in chunks:
            await db.refresh(chunk, ["document"])
        chunks = apply_content_type_boost(chunks)

    return chunks


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

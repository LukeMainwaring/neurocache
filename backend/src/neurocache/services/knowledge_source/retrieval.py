"""Retrieval service for semantic and hybrid search over document chunks."""

import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.document_chunk import DocumentChunk
from neurocache.schemas.knowledge_source.document import ContentType
from neurocache.services.embedding import generate_embedding

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 10
RAG_SIMILARITY_THRESHOLD = 0.3  # Minimum similarity to include in the RAG context
RRF_K = 60  # Standard Reciprocal Rank Fusion constant
HYBRID_CANDIDATE_MULTIPLIER = 2  # Fetch 2x candidates per method before fusion

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


def reciprocal_rank_fusion(
    semantic_results: list[tuple[DocumentChunk, float]],
    keyword_results: list[tuple[DocumentChunk, float]],
    k: int = RRF_K,
) -> list[tuple[DocumentChunk, float]]:
    """Fuse two ranked result lists using Reciprocal Rank Fusion.

    Each result list contributes score = 1/(k + rank) where rank is 1-indexed.
    Chunks appearing in both lists get summed scores, naturally ranking higher
    than chunks appearing in only one list.

    Args:
        semantic_results: Ranked results from semantic (vector) search
        keyword_results: Ranked results from keyword (full-text) search
        k: RRF constant (default 60). Higher values reduce the influence of
           high-ranking items, making the fusion more uniform.

    Returns:
        Fused results sorted by combined RRF score descending.
    """
    fused: dict[int, tuple[DocumentChunk, float]] = {}

    for rank, (chunk, _score) in enumerate(semantic_results, start=1):
        rrf_score = 1.0 / (k + rank)
        fused[chunk.id] = (chunk, rrf_score)

    for rank, (chunk, _score) in enumerate(keyword_results, start=1):
        rrf_score = 1.0 / (k + rank)
        if chunk.id in fused:
            existing_chunk, existing_score = fused[chunk.id]
            fused[chunk.id] = (existing_chunk, existing_score + rrf_score)
        else:
            fused[chunk.id] = (chunk, rrf_score)

    results = list(fused.values())
    results.sort(key=lambda x: x[1], reverse=True)
    return results


async def search_hybrid_for_user(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    query: str,
    user_id: str,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = RAG_SIMILARITY_THRESHOLD,
    content_types: list[ContentType] | None = None,
    apply_boost: bool = True,
) -> list[tuple[DocumentChunk, float]]:
    """Hybrid search combining semantic and keyword retrieval with RRF.

    Runs both search methods, fuses results using Reciprocal Rank Fusion,
    and applies content-type boosting. This improves recall for exact keyword
    matches (proper nouns, book titles, author names) while preserving
    semantic search's strength for conceptual queries.

    Args:
        db: Database session
        openai_client: OpenAI client for generating query embedding
        query: The search query text
        user_id: Filter to chunks from this user's knowledge sources
        top_k: Maximum number of results to return
        similarity_threshold: Minimum similarity score for semantic search
        content_types: Optional list of content types to filter by
        apply_boost: Whether to apply content-type-aware score boosting

    Returns:
        List of (DocumentChunk, rrf_score) tuples, ordered by fused score descending.
    """
    type_values = [ct.value for ct in content_types] if content_types else None
    candidate_count = top_k * HYBRID_CANDIDATE_MULTIPLIER

    # Generate embedding first (requires OpenAI API call)
    query_embedding = await generate_embedding(openai_client, query)

    # Run semantic and keyword searches sequentially (AsyncSession is not
    # safe for concurrent use -- it wraps a single underlying connection)
    semantic_results = await DocumentChunk.search_similar_for_user(
        db, query_embedding, user_id, candidate_count, similarity_threshold, type_values
    )
    keyword_results = await DocumentChunk.search_keyword_for_user(db, query, user_id, candidate_count, type_values)

    logger.info(f"Hybrid search: {len(semantic_results)} semantic, {len(keyword_results)} keyword results")

    # Fuse, normalize to 0-1 range, and trim
    fused = reciprocal_rank_fusion(semantic_results, keyword_results)
    if fused:
        max_score = fused[0][1]  # highest score (already sorted descending)
        fused = [(chunk, score / max_score) for chunk, score in fused]
    fused = fused[:top_k]

    # Apply content-type boosting if enabled and we have results
    if apply_boost and fused:
        for chunk, _ in fused:
            await db.refresh(chunk, ["document"])
        fused = apply_content_type_boost(fused)

    return fused

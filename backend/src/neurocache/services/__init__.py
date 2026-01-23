"""Services for business logic."""

from .embedding import generate_embedding, generate_embeddings_batch
from .retrieval import (
    get_chunk_with_context,
    search_similar_chunks,
    search_similar_chunks_for_user,
)

__all__ = [
    "generate_embedding",
    "generate_embeddings_batch",
    "search_similar_chunks",
    "search_similar_chunks_for_user",
    "get_chunk_with_context",
]

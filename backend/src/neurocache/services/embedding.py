"""Embedding service for generating vector embeddings via OpenAI."""

import logging

from openai import AsyncOpenAI

from neurocache.core.config import get_settings

logger = logging.getLogger(__name__)

config = get_settings()


async def generate_embedding(openai_client: AsyncOpenAI, text: str) -> list[float]:
    """Generate a vector embedding for the given text.

    Args:
        openai_client: OpenAI client
        text: The text to embed

    Returns:
        A list of floats representing the embedding vector (1536 dimensions)

    Raises:
        OpenAIError: If the API call fails
    """
    response = await openai_client.embeddings.create(
        model=config.EMBEDDING_MODEL,
        input=text,
        dimensions=config.EMBEDDING_DIMENSION,
    )

    return response.data[0].embedding


async def generate_embeddings_batch(openai_client: AsyncOpenAI, texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call.

    More efficient than calling generate_embedding multiple times.
    OpenAI supports up to 2048 texts per batch.

    Args:
        openai_client: OpenAI client
        texts: List of texts to embed

    Returns:
        List of embedding vectors, one per input text (in same order)

    Raises:
        OpenAIError: If the API call fails
    """
    if not texts:
        return []

    response = await openai_client.embeddings.create(
        model=config.EMBEDDING_MODEL,
        input=texts,
        dimensions=config.EMBEDDING_DIMENSION,
    )

    # Sort by index to ensure order matches input
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]

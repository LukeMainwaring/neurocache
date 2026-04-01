import logging

from openai import AsyncOpenAI

from neurocache.core.config import get_settings

logger = logging.getLogger(__name__)

config = get_settings()


async def generate_embedding(openai_client: AsyncOpenAI, text: str) -> list[float]:
    response = await openai_client.embeddings.create(
        model=config.EMBEDDING_MODEL,
        input=text,
        dimensions=config.EMBEDDING_DIMENSION,
    )

    return response.data[0].embedding


# OpenAI embedding API limits
MAX_TOKENS_PER_REQUEST = 250_000  # Use 250k to leave buffer under 300k limit
CHARS_PER_TOKEN_ESTIMATE = 3  # Conservative estimate (technical text can be ~2-3 chars/token)


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN_ESTIMATE


async def generate_embeddings_batch(openai_client: AsyncOpenAI, texts: list[str]) -> list[list[float]]:
    """Splits into multiple API calls if total tokens exceed the per-request limit."""
    if not texts:
        return []

    # Split texts into batches that fit under the token limit
    batches: list[list[str]] = []
    current_batch: list[str] = []
    current_tokens = 0

    for text in texts:
        text_tokens = _estimate_tokens(text)

        # If adding this text exceeds the limit, start a new batch
        if current_tokens + text_tokens > MAX_TOKENS_PER_REQUEST and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(text)
        current_tokens += text_tokens

    # Don't forget the last batch
    if current_batch:
        batches.append(current_batch)

    logger.info(f"Embedding {len(texts)} texts in {len(batches)} batches")

    # Process each batch and collect results
    all_embeddings: list[list[float]] = []

    for batch in batches:
        response = await openai_client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=batch,
            dimensions=config.EMBEDDING_DIMENSION,
        )

        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend([item.embedding for item in sorted_data])

    return all_embeddings

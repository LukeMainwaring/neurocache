"""Ingestion service for processing documents into chunks with embeddings."""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.document import Document
from neurocache.models.document_chunk import DocumentChunk
from neurocache.schemas.document import DocumentStatus
from neurocache.services.embedding import generate_embeddings_batch

logger = logging.getLogger(__name__)

# Container path where vault is mounted
VAULT_MOUNT_PATH = "/vault"

# TODO: experiment with different chunking strategies. ideal size, how to break them up, how to overlap them, etc.
# Chunking config
MAX_CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 100  # characters of overlap between chunks


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def naive_chunk_text(text: str, max_size: int = MAX_CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into chunks with overlap.

    Simple chunking strategy that splits on paragraph boundaries when possible.

    Args:
        text: The text to chunk
        max_size: Maximum characters per chunk
        overlap: Characters of overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to find a paragraph break near the end
        chunk = text[start:end]
        last_para = chunk.rfind("\n\n")
        if last_para > max_size // 2:
            end = start + last_para + 2  # Include the newlines

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]  # Filter empty chunks


def extract_title_from_markdown(content: str) -> str | None:
    """Extract title from markdown content.

    Looks for first H1 heading or first line if no heading found.
    """
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


async def ingest_document(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    knowledge_source_id: str,
    relative_path: str,
) -> Document:
    """Ingest a single document from a knowledge source.

    Reads the file, chunks it, generates embeddings, and stores in the database.

    Args:
        db: Database session
        openai_client: OpenAI client for embeddings
        knowledge_source_id: The knowledge source this document belongs to
        relative_path: Path relative to the knowledge source root (e.g., "TODO.md")

    Returns:
        The created Document record

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty
    """
    file_path = Path(VAULT_MOUNT_PATH) / relative_path

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read file content and metadata
    content = file_path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"File is empty: {file_path}")

    file_stat = file_path.stat()
    file_modified_at = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)

    # Create document record
    content_hash = compute_content_hash(content)
    title = extract_title_from_markdown(content)

    document = Document(
        id=uuid.uuid4(),
        knowledge_source_id=knowledge_source_id,
        relative_path=relative_path,
        title=title,
        content_hash=content_hash,
        file_modified_at=file_modified_at,
        status=DocumentStatus.PROCESSING,
    )
    db.add(document)
    await db.flush()  # Get the document ID

    logger.info("Created document %s for %s", document.id, relative_path)

    # Chunk the content
    chunks = naive_chunk_text(content)
    logger.info("Split document into %d chunks", len(chunks))

    # Generate embeddings in batch
    embeddings = await generate_embeddings_batch(openai_client, chunks)

    # Create chunk records
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        chunk = DocumentChunk(
            document_id=document.id,
            content=chunk_text,
            chunk_index=i,
            embedding=embedding,
            token_count=len(chunk_text) // 4,  # Rough estimate
        )
        db.add(chunk)

    # Update document status
    document.status = DocumentStatus.INDEXED
    document.chunk_count = len(chunks)
    document.indexed_at = datetime.now(timezone.utc)

    await db.flush()
    logger.info("Indexed document %s with %d chunks", document.id, len(chunks))

    return document

"""Ingestion service for processing documents into chunks with embeddings."""

import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.document import Document
from neurocache.models.document_chunk import DocumentChunk
from neurocache.schemas.document import (
    BatchIngestFailure,
    BatchIngestResult,
    DocumentCreateSchema,
    DocumentStatus,
    DocumentUpdateSchema,
)
from neurocache.services.embedding import generate_embeddings_batch

logger = logging.getLogger(__name__)

# Container path where vault is mounted
VAULT_MOUNT_PATH = "/vault"

# Directories to exclude during batch ingestion
DEFAULT_EXCLUDE_DIRS = {".obsidian", ".smart-env", "copilot", ".git", ".trash"}

# Chunking config
TARGET_CHUNK_SIZE = 1500  # target characters per chunk
MAX_CHUNK_SIZE = 2000  # ceiling - never exceed this
CHUNK_OVERLAP = 200  # characters of overlap between chunks
MIN_CHUNK_SIZE = 300  # avoid creating orphan chunks smaller than this

# Pattern to detect YAML frontmatter at the start of a file
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.DOTALL)

# Pattern to detect date entries at start of line (e.g., "January 14, 2024" or "5/15/2019")
DATE_PATTERN = re.compile(
    r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}|"
    r"^\d{1,2}/\d{1,2}/\d{4}",
    re.MULTILINE,
)

# Pattern to detect markdown headers
HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from the start of a document."""
    return FRONTMATTER_PATTERN.sub("", text, count=1)


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def detect_sections(text: str) -> list[tuple[str, str, int]]:
    """Split text into sections based on headers and date patterns.

    Sections are detected in priority order:
    1. Markdown headers (# through ######)
    2. Date patterns at line start (e.g., "January 14, 2024" or "5/15/2019")

    For header sections, the header line itself is excluded from section_content
    since it's already captured in the section_header field (avoids duplication
    when the header is injected as chunk context).

    Args:
        text: The full document text

    Returns:
        List of (section_header, section_content, start_position) tuples.
        If no sections are found, returns single entry with empty header.
    """
    # Find all section boundaries
    # Each boundary: (boundary_pos, content_start, header_text)
    #   boundary_pos: where this section starts (used to end previous section)
    #   content_start: where the actual body content begins (after header line for headers)
    boundaries: list[tuple[int, int, str]] = []

    # Find markdown headers - content starts after the header line
    for match in HEADER_PATTERN.finditer(text):
        header_text = match.group(2).strip()
        boundaries.append((match.start(), match.end(), header_text))

    # Find date entries - date is part of the content itself
    for match in DATE_PATTERN.finditer(text):
        date_text = match.group(0).strip()
        boundaries.append((match.start(), match.start(), date_text))

    # Sort by position
    boundaries.sort(key=lambda x: x[0])

    if not boundaries:
        # No sections found - return entire text as single section
        return [("", text, 0)]

    sections: list[tuple[str, str, int]] = []

    # Handle content before first section (if any)
    if boundaries[0][0] > 0:
        preamble = text[: boundaries[0][0]].strip()
        if preamble:
            sections.append(("", preamble, 0))

    # Extract each section
    for i, (boundary_pos, content_start, header) in enumerate(boundaries):
        # End of this section is the start of the next boundary, or end of text
        if i + 1 < len(boundaries):
            end_pos = boundaries[i + 1][0]
        else:
            end_pos = len(text)

        section_content = text[content_start:end_pos].strip()
        if section_content:
            sections.append((header, section_content, boundary_pos))

    return sections


def split_section_with_overlap(
    content: str,
    max_size: int = MAX_CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    min_size: int = MIN_CHUNK_SIZE,
) -> list[str]:
    """Split a section that exceeds max_size on paragraph breaks with overlap.

    Args:
        content: Section content to split
        max_size: Maximum characters per chunk
        overlap: Characters of overlap between chunks
        min_size: Minimum chunk size (smaller chunks merged with previous)

    Returns:
        List of text chunks
    """
    if len(content) <= max_size:
        return [content]

    chunks: list[str] = []
    start = 0

    while start < len(content):
        end = start + max_size
        if end >= len(content):
            final_chunk = content[start:].strip()
            if final_chunk:
                # If this final chunk is too small, merge with previous
                if len(final_chunk) < min_size and chunks:
                    chunks[-1] = chunks[-1] + "\n\n" + final_chunk
                else:
                    chunks.append(final_chunk)
            break

        # Try to find a paragraph break near the end
        chunk = content[start:end]
        last_paragraph = chunk.rfind("\n\n")

        if last_paragraph > max_size // 2:
            end = start + last_paragraph + 2  # Include the newlines

        chunk_text = content[start:end].strip()
        if chunk_text:
            chunks.append(chunk_text)

        start = end - overlap

    return chunks


def markdown_aware_chunk_text(
    text: str,
    filename: str,
    target_size: int = TARGET_CHUNK_SIZE,
    max_size: int = MAX_CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    min_size: int = MIN_CHUNK_SIZE,
) -> list[str]:
    """Chunk text respecting markdown structure with context injection.

    This function:
    1. Detects sections based on headers and date patterns
    2. Keeps small sections intact, splits large ones on paragraph breaks
    3. Prepends context (filename, section header) to each chunk
    4. Merges orphan chunks that are too small

    Args:
        text: The full document text
        filename: Source filename for context injection
        target_size: Target chunk size (used for small file detection)
        max_size: Maximum chunk size before splitting
        overlap: Characters of overlap when splitting large sections
        min_size: Minimum chunk size (smaller chunks get merged)

    Returns:
        List of context-injected text chunks
    """
    text = strip_frontmatter(text)

    # Small files: return as single chunk
    if len(text) <= target_size:
        context = f"[Source: {filename}]\n\n"
        return [context + text.strip()]

    sections = detect_sections(text)
    chunks: list[str] = []

    for section_header, section_content, _ in sections:
        # Build context prefix
        if section_header:
            context = f"[Source: {filename}]\n[Section: {section_header}]\n\n"
        else:
            context = f"[Source: {filename}]\n\n"

        context_len = len(context)
        available_size = max_size - context_len

        if len(section_content) <= available_size:
            # Section fits in one chunk
            chunks.append(context + section_content)
        else:
            # Split section on paragraph breaks
            section_chunks = split_section_with_overlap(
                section_content, max_size=available_size, overlap=overlap, min_size=min_size
            )
            for chunk_text in section_chunks:
                chunks.append(context + chunk_text)

    # Final pass: merge any orphan chunks that are too small
    merged_chunks: list[str] = []
    for chunk in chunks:
        if merged_chunks and len(chunk) < min_size:
            # Merge with previous chunk
            merged_chunks[-1] = merged_chunks[-1] + "\n\n" + chunk
        else:
            merged_chunks.append(chunk)

    return merged_chunks


async def ingest_document(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    knowledge_source_id: uuid.UUID,
    relative_path: str,
) -> Document:
    """Ingest a single document from a knowledge source.

    Reads the file, chunks it, generates embeddings, and stores in the database.

    Args:
        db: Database session
        openai_client: OpenAI client for embeddings
        knowledge_source_id: The knowledge source this document belongs to
        relative_path: Path relative to the knowledge source root (e.g., "Brain Dump.md")

    Returns:
        The created Document record

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty
    """
    file_path = Path(VAULT_MOUNT_PATH) / relative_path

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"File is empty: {file_path}")

    file_stat = file_path.stat()
    file_modified_at = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)

    content_hash = compute_content_hash(content)
    title = Path(relative_path).stem

    document = await Document.create(
        db,
        DocumentCreateSchema(
            knowledge_source_id=knowledge_source_id,
            relative_path=relative_path,
            title=title,
            content_hash=content_hash,
            file_modified_at=file_modified_at,
            status=DocumentStatus.PROCESSING,
        ),
    )
    logger.info("Created document %s for %s", document.id, relative_path)

    filename = Path(relative_path).name
    chunks = markdown_aware_chunk_text(content, filename)
    logger.info("Split document into %d chunks", len(chunks))

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

    document = await Document.update(
        db,
        document.id,
        DocumentUpdateSchema(
            status=DocumentStatus.INDEXED,
            chunk_count=len(chunks),
            indexed_at=datetime.now(timezone.utc),
        ),
    )
    logger.info("Indexed document %s with %d chunks", document.id, len(chunks))
    return document


def discover_markdown_files(
    base_path: Path,
    exclude_dirs: set[str] | None = None,
) -> list[str]:
    """Recursively find all .md files, excluding system directories.

    Args:
        base_path: Root directory to search
        exclude_dirs: Directory names to skip (defaults to DEFAULT_EXCLUDE_DIRS)

    Returns:
        List of relative paths to markdown files
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    markdown_files: list[str] = []

    for file_path in base_path.rglob("*.md"):
        # Check if any parent directory should be excluded
        parts = file_path.relative_to(base_path).parts
        if any(part in exclude_dirs for part in parts[:-1]):  # Exclude dirs, not filename
            continue
        markdown_files.append(str(file_path.relative_to(base_path)))

    return sorted(markdown_files)


def _file_has_changed(existing_doc: Document, file_path: Path) -> tuple[bool, str | None]:
    """Check if a file's content has changed since last ingestion.

    Uses a two-stage check:
    1. Fast: compare mtime — if unchanged, skip reading file
    2. Slow: read file and compare content hash

    Returns:
        (has_changed, new_content_hash) — hash is None if unchanged
    """
    file_stat = file_path.stat()
    current_mtime = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)

    # Fast check: if mtime is the same, content hasn't changed
    if existing_doc.file_modified_at and current_mtime == existing_doc.file_modified_at:
        return False, None

    # mtime differs — read file and compare content hash
    content = file_path.read_text(encoding="utf-8")
    current_hash = compute_content_hash(content)

    if current_hash == existing_doc.content_hash:
        return False, None  # mtime changed but content is the same (e.g., touch)

    return True, current_hash


async def ingest_all_documents(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    knowledge_source_id: uuid.UUID,
    force_reindex: bool = False,
) -> BatchIngestResult:
    """Ingest all markdown documents from a knowledge source.

    Args:
        db: Database session
        openai_client: OpenAI client for embeddings
        knowledge_source_id: The knowledge source to ingest from
        force_reindex: If True, re-ingest documents even if already indexed

    Returns:
        BatchIngestResult with statistics about the operation
    """
    start_time = time.time()

    base_path = Path(VAULT_MOUNT_PATH)
    markdown_files = discover_markdown_files(base_path)

    total_files = len(markdown_files)
    documents_created = 0
    documents_updated = 0
    documents_skipped = 0
    documents_failed = 0
    failed_files: list[BatchIngestFailure] = []

    logger.info("Discovered %d markdown files to process", total_files)

    for relative_path in markdown_files:
        try:
            existing_doc = await Document.get_by_relative_path(db, knowledge_source_id, relative_path)
            if existing_doc:
                if force_reindex:
                    await Document.delete(db, existing_doc.id)
                    logger.info("Deleted existing document for re-indexing: %s", relative_path)
                else:
                    file_path = Path(VAULT_MOUNT_PATH) / relative_path
                    changed, _ = _file_has_changed(existing_doc, file_path)
                    if not changed:
                        documents_skipped += 1
                        logger.debug("Skipping unchanged: %s", relative_path)
                        continue
                    # Content changed — delete and re-ingest
                    await Document.delete(db, existing_doc.id)
                    logger.info("Re-indexing modified document: %s", relative_path)
                    await ingest_document(db, openai_client, knowledge_source_id, relative_path)
                    documents_updated += 1
                    continue

            await ingest_document(db, openai_client, knowledge_source_id, relative_path)
            documents_created += 1

        except Exception as e:
            documents_failed += 1
            error_msg = str(e)
            failed_files.append(BatchIngestFailure(relative_path=relative_path, error=error_msg))
            logger.warning("Failed to ingest %s: %s", relative_path, error_msg)

    # Detect deleted files — remove DB records for files no longer on disk
    discovered_set = set(markdown_files)
    all_docs = await Document.get_all_by_source(db, knowledge_source_id)
    documents_deleted = 0
    for doc in all_docs:
        if doc.relative_path not in discovered_set:
            await Document.delete(db, doc.id)
            documents_deleted += 1
            logger.info("Deleted document no longer on disk: %s", doc.relative_path)

    duration = time.time() - start_time
    logger.info(
        "Batch ingestion complete: %d created, %d updated, %d deleted, %d skipped, %d failed in %.2fs",
        documents_created,
        documents_updated,
        documents_deleted,
        documents_skipped,
        documents_failed,
        duration,
    )
    return BatchIngestResult(
        total_files_found=total_files,
        documents_created=documents_created,
        documents_updated=documents_updated,
        documents_deleted=documents_deleted,
        documents_skipped=documents_skipped,
        documents_failed=documents_failed,
        failed_files=failed_files,
        duration_seconds=round(duration, 2),
    )

"""Ingestion service for processing documents into chunks with embeddings."""

import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.models.document import Document
from neurocache.models.document_chunk import DocumentChunk
from neurocache.schemas.knowledge_source.document import (
    BOOKS_DIR,
    BatchIngestFailure,
    BatchIngestResult,
    BookPdfPreview,
    BookSchema,
    ContentType,
    DocumentCreateSchema,
    DocumentStatus,
    DocumentUpdateSchema,
)
from neurocache.schemas.knowledge_source.document_chunk import ChunkData
from neurocache.services.embedding import generate_embeddings_batch
from neurocache.services.knowledge_source.pdf_chunker import chunk_pdf_pages
from neurocache.services.knowledge_source.pdf_parser import extract_pdf_content

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


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse YAML frontmatter from the start of a document.

    Returns a dict of key-value pairs from the frontmatter.
    Only handles simple key: value pairs (not nested structures).

    Args:
        text: The full document text

    Returns:
        Dict of frontmatter fields, empty if no frontmatter found
    """
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}

    frontmatter_block = match.group(0)
    # Remove the --- delimiters
    lines = frontmatter_block.strip().split("\n")[1:-1]

    result: dict[str, str] = {}
    for line in lines:
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            result[key] = value

    return result


def detect_content_type(frontmatter: dict[str, str], relative_path: str, is_pdf: bool = False) -> ContentType:
    """Detect content type from frontmatter or file path.

    Priority:
    1. PDF files in Books/ -> BOOK_SOURCE
    2. Explicit 'type' field in frontmatter
    3. Path-based detection (Books/ folder)
    4. Default to personal_note

    Args:
        frontmatter: Parsed frontmatter dict
        relative_path: Path relative to vault root
        is_pdf: Whether the file is a PDF

    Returns:
        Detected ContentType
    """
    in_books_dir = relative_path.startswith(f"{BOOKS_DIR}/")

    # PDFs in Books/ are book sources
    if is_pdf:
        return ContentType.BOOK_SOURCE if in_books_dir else ContentType.PERSONAL_NOTE

    fm_type = frontmatter.get("type", "").lower()

    if fm_type == "book":
        return ContentType.BOOK_NOTE
    elif fm_type == "article":
        return ContentType.ARTICLE

    # Path-based detection as fallback
    if in_books_dir:
        return ContentType.BOOK_NOTE
    elif relative_path.startswith("Articles/"):
        return ContentType.ARTICLE

    return ContentType.PERSONAL_NOTE


def extract_book_metadata(frontmatter: dict[str, str]) -> dict[str, str]:
    """Extract book-specific metadata from frontmatter.

    Args:
        frontmatter: Parsed frontmatter dict

    Returns:
        Dict with book metadata fields (author, title, date_read, rating)
    """
    book_fields = ["author", "title", "date_read", "rating", "tags"]
    return {k: v for k, v in frontmatter.items() if k in book_fields and v}


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
    target_size: int = TARGET_CHUNK_SIZE,
    max_size: int = MAX_CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    min_size: int = MIN_CHUNK_SIZE,
) -> list[ChunkData]:
    """Chunk text respecting markdown structure.

    This function:
    1. Detects sections based on headers and date patterns
    2. Keeps small sections intact, splits large ones on paragraph breaks
    3. Returns ChunkData with raw content and section metadata (no context prefixes)
    4. Merges orphan chunks that are too small

    Args:
        text: The full document text
        target_size: Target chunk size (used for small file detection)
        max_size: Maximum chunk size before splitting
        overlap: Characters of overlap when splitting large sections
        min_size: Minimum chunk size (smaller chunks get merged)

    Returns:
        List of ChunkData with raw content and section metadata
    """
    text = strip_frontmatter(text)

    # Small files: return as single chunk
    if len(text) <= target_size:
        return [ChunkData(content=text.strip())]

    sections = detect_sections(text)
    chunks: list[ChunkData] = []

    for section_header, section_content, _ in sections:
        header = section_header or None

        if len(section_content) <= max_size:
            # Section fits in one chunk
            chunks.append(ChunkData(content=section_content, section_header=header))
        else:
            # Split section on paragraph breaks
            section_chunks = split_section_with_overlap(
                section_content, max_size=max_size, overlap=overlap, min_size=min_size
            )
            for chunk_text in section_chunks:
                chunks.append(ChunkData(content=chunk_text, section_header=header))

    # Final pass: merge any orphan chunks that are too small
    merged_chunks: list[ChunkData] = []
    for chunk in chunks:
        if merged_chunks and len(chunk.content) < min_size:
            # Merge with previous chunk, keep earlier chunk's section_header
            merged_chunks[-1] = ChunkData(
                content=merged_chunks[-1].content + "\n\n" + chunk.content,
                section_header=merged_chunks[-1].section_header,
            )
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

    frontmatter = parse_frontmatter(content)
    content_type = detect_content_type(frontmatter, relative_path)

    # Build doc_metadata from frontmatter
    doc_metadata: dict[str, str] | None = None
    if content_type == ContentType.BOOK_NOTE:
        book_meta = extract_book_metadata(frontmatter)
        if book_meta:
            doc_metadata = book_meta
            # Use frontmatter title if available (often more complete than filename)
            if "title" in book_meta:
                title = book_meta["title"]

    logger.info(f"Detected content type '{content_type}' for {relative_path}")

    document = await Document.create(
        db,
        DocumentCreateSchema(
            knowledge_source_id=knowledge_source_id,
            relative_path=relative_path,
            title=title,
            content_type=content_type,
            content_hash=content_hash,
            file_modified_at=file_modified_at,
            doc_metadata=doc_metadata,
            status=DocumentStatus.PROCESSING,
        ),
    )
    logger.info(f"Created document {document.id} for {relative_path}")

    try:
        chunk_data_list = markdown_aware_chunk_text(content)
        logger.info(f"Split document into {len(chunk_data_list)} chunks")

        # Embed only raw content (no context prefixes)
        embeddings = await generate_embeddings_batch(openai_client, [cd.content for cd in chunk_data_list])

        # Create chunk records
        for i, (cd, embedding) in enumerate(zip(chunk_data_list, embeddings, strict=True)):
            chunk = DocumentChunk(
                document_id=document.id,
                content=cd.content,
                chunk_index=i,
                embedding=embedding,
                chunk_metadata=cd.chunk_metadata,
                token_count=cd.token_count,
            )
            db.add(chunk)

        document = await Document.update(
            db,
            document.id,
            DocumentUpdateSchema(
                status=DocumentStatus.INDEXED,
                chunk_count=len(chunk_data_list),
                indexed_at=datetime.now(timezone.utc),
            ),
        )
        logger.info(f"Indexed document {document.id} with {len(chunk_data_list)} chunks")
        return document

    except Exception as e:
        # Update document status to ERROR on failure
        await Document.update(
            db,
            document.id,
            DocumentUpdateSchema(
                status=DocumentStatus.ERROR,
                error_message=str(e)[:500],  # Truncate long error messages
            ),
        )
        raise


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


def discover_pdf_files(
    base_path: Path,
    exclude_dirs: set[str] | None = None,
) -> list[str]:
    """Find PDF files in the Books/ directory.

    Only searches within the top-level Books/ directory.
    PDFs outside this directory are ignored.

    Args:
        base_path: Root directory to search
        exclude_dirs: Directory names to skip (defaults to DEFAULT_EXCLUDE_DIRS)

    Returns:
        List of relative paths to PDF files
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    books_path = base_path / BOOKS_DIR
    if not books_path.exists():
        return []

    pdf_files: list[str] = []

    for file_path in books_path.rglob("*.pdf"):
        parts = file_path.relative_to(base_path).parts
        # Check if any parent directory should be excluded
        if any(part in exclude_dirs for part in parts[:-1]):
            continue
        pdf_files.append(str(file_path.relative_to(base_path)))

    return sorted(pdf_files)


async def _auto_link_book_documents(
    db: AsyncSession,
    knowledge_source_id: uuid.UUID,
    document: Document,
) -> None:
    """Link a document to other documents in the same book folder.

    PDFs get linked to book notes and vice versa when they share
    the same book folder (e.g., "Books/AI Engineering/").

    Args:
        db: Database session
        knowledge_source_id: Knowledge source ID
        document: The document to link
    """
    book_folder = BookSchema.folder_from_path(document.relative_path)
    if not book_folder:
        return

    # Find other documents in the same book folder
    all_docs = await Document.get_all_by_source(db, knowledge_source_id)

    for other_doc in all_docs:
        if other_doc.id == document.id:
            continue

        other_folder = BookSchema.folder_from_path(other_doc.relative_path)
        if other_folder != book_folder:
            continue

        # Link PDF to book note (and vice versa)
        is_current_pdf = document.relative_path.lower().endswith(".pdf")
        is_other_pdf = other_doc.relative_path.lower().endswith(".pdf")

        if is_current_pdf != is_other_pdf:
            # Store the link in doc_metadata
            current_metadata = document.doc_metadata or {}
            current_metadata["linked_document_id"] = str(other_doc.id)
            await Document.update(
                db,
                document.id,
                DocumentUpdateSchema(doc_metadata=current_metadata),
            )

            # Also link the other document back
            other_metadata = other_doc.doc_metadata or {}
            other_metadata["linked_document_id"] = str(document.id)
            await Document.update(
                db,
                other_doc.id,
                DocumentUpdateSchema(doc_metadata=other_metadata),
            )

            logger.info(f"Auto-linked documents: {document.relative_path} <-> {other_doc.relative_path}")
            break  # Only link to one document


async def ingest_pdf_document(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    knowledge_source_id: uuid.UUID,
    relative_path: str,
) -> Document:
    """Ingest a PDF document from a knowledge source.

    Extracts text from the PDF, chunks it respecting chapter boundaries,
    generates embeddings, and stores in the database.

    Args:
        db: Database session
        openai_client: OpenAI client for embeddings
        knowledge_source_id: The knowledge source this document belongs to
        relative_path: Path relative to the knowledge source root

    Returns:
        The created Document record

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the PDF is password-protected or has no extractable text
    """
    file_path = Path(VAULT_MOUNT_PATH) / relative_path

    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    file_stat = file_path.stat()
    file_modified_at = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)

    # Extract PDF content
    pages = extract_pdf_content(file_path)

    # Compute hash from extracted text for change detection
    all_text = "\n".join(p.text for p in pages)
    content_hash = compute_content_hash(all_text)
    title = Path(relative_path).stem

    # Detect content type (will be BOOK_SOURCE for PDFs in book directories)
    content_type = detect_content_type({}, relative_path, is_pdf=True)

    logger.info(f"Detected content type '{content_type}' for PDF {relative_path}")

    document = await Document.create(
        db,
        DocumentCreateSchema(
            knowledge_source_id=knowledge_source_id,
            relative_path=relative_path,
            title=title,
            content_type=content_type,
            content_hash=content_hash,
            file_modified_at=file_modified_at,
            status=DocumentStatus.PROCESSING,
        ),
    )
    logger.info(f"Created PDF document {document.id} for {relative_path}")

    try:
        # Chunk the PDF content
        chunk_data_list = chunk_pdf_pages(pages)
        logger.info(f"Split PDF into {len(chunk_data_list)} chunks")

        if not chunk_data_list:
            # No chunks created (empty PDF)
            document = await Document.update(
                db,
                document.id,
                DocumentUpdateSchema(
                    status=DocumentStatus.INDEXED,
                    chunk_count=0,
                    indexed_at=datetime.now(timezone.utc),
                ),
            )
            return document

        # Generate embeddings
        embeddings = await generate_embeddings_batch(openai_client, [cd.content for cd in chunk_data_list])

        # Create chunk records
        for i, (cd, embedding) in enumerate(zip(chunk_data_list, embeddings, strict=True)):
            chunk = DocumentChunk(
                document_id=document.id,
                content=cd.content,
                chunk_index=i,
                embedding=embedding,
                chunk_metadata=cd.chunk_metadata,
                token_count=cd.token_count,
            )
            db.add(chunk)

        document = await Document.update(
            db,
            document.id,
            DocumentUpdateSchema(
                status=DocumentStatus.INDEXED,
                chunk_count=len(chunk_data_list),
                indexed_at=datetime.now(timezone.utc),
            ),
        )
        logger.info(f"Indexed PDF document {document.id} with {len(chunk_data_list)} chunks")

        # Auto-link to book notes in the same folder
        await _auto_link_book_documents(db, knowledge_source_id, document)

        return document

    except Exception as e:
        # Update document status to ERROR on failure
        await Document.update(
            db,
            document.id,
            DocumentUpdateSchema(
                status=DocumentStatus.ERROR,
                error_message=str(e)[:500],  # Truncate long error messages
            ),
        )
        raise


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
    """Ingest all documents (markdown and PDF) from a knowledge source.

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
    pdf_files = discover_pdf_files(base_path)

    # Combine all files for tracking
    all_files = markdown_files + pdf_files
    total_files = len(all_files)
    documents_created = 0
    documents_updated = 0
    documents_skipped = 0
    documents_failed = 0
    failed_files: list[BatchIngestFailure] = []

    logger.info(f"Discovered {len(markdown_files)} markdown files and {len(pdf_files)} PDF files to process")

    # Process markdown files
    for relative_path in markdown_files:
        try:
            existing_doc = await Document.get_by_relative_path(db, knowledge_source_id, relative_path)
            if existing_doc:
                if force_reindex:
                    await Document.delete(db, existing_doc.id)
                    logger.info(f"Deleted existing document for re-indexing: {relative_path}")
                else:
                    file_path = Path(VAULT_MOUNT_PATH) / relative_path
                    changed, _ = _file_has_changed(existing_doc, file_path)
                    if not changed:
                        documents_skipped += 1
                        logger.debug(f"Skipping unchanged: {relative_path}")
                        continue
                    # Content changed — delete and re-ingest
                    await Document.delete(db, existing_doc.id)
                    logger.info(f"Re-indexing modified document: {relative_path}")
                    await ingest_document(db, openai_client, knowledge_source_id, relative_path)
                    documents_updated += 1
                    continue

            await ingest_document(db, openai_client, knowledge_source_id, relative_path)
            documents_created += 1

        except Exception as e:
            documents_failed += 1
            error_msg = str(e)
            failed_files.append(BatchIngestFailure(relative_path=relative_path, error=error_msg))
            logger.warning(f"Failed to ingest {relative_path}: {error_msg}")

    # Process PDF files
    for relative_path in pdf_files:
        try:
            existing_doc = await Document.get_by_relative_path(db, knowledge_source_id, relative_path)
            if existing_doc:
                if force_reindex:
                    await Document.delete(db, existing_doc.id)
                    logger.info(f"Deleted existing PDF for re-indexing: {relative_path}")
                else:
                    file_path = Path(VAULT_MOUNT_PATH) / relative_path
                    # For PDFs, just check mtime (content hash would require re-extracting)
                    file_stat = file_path.stat()
                    current_mtime = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
                    if existing_doc.file_modified_at and current_mtime == existing_doc.file_modified_at:
                        documents_skipped += 1
                        logger.debug(f"Skipping unchanged PDF: {relative_path}")
                        continue
                    # mtime changed — delete and re-ingest
                    await Document.delete(db, existing_doc.id)
                    logger.info(f"Re-indexing modified PDF: {relative_path}")
                    await ingest_pdf_document(db, openai_client, knowledge_source_id, relative_path)
                    documents_updated += 1
                    continue

            await ingest_pdf_document(db, openai_client, knowledge_source_id, relative_path)
            documents_created += 1

        except Exception as e:
            documents_failed += 1
            error_msg = str(e)
            failed_files.append(BatchIngestFailure(relative_path=relative_path, error=error_msg))
            logger.warning(f"Failed to ingest PDF {relative_path}: {error_msg}")

    # Detect deleted files — remove DB records for files no longer on disk
    discovered_set = set(all_files)
    all_docs = await Document.get_all_by_source(db, knowledge_source_id)
    documents_deleted = 0
    for doc in all_docs:
        if doc.relative_path not in discovered_set:
            await Document.delete(db, doc.id)
            documents_deleted += 1
            logger.info(f"Deleted document no longer on disk: {doc.relative_path}")

    duration = time.time() - start_time
    logger.info(
        f"Batch ingestion complete: {documents_created} created, {documents_updated} updated, {documents_deleted} deleted, {documents_skipped} skipped, {documents_failed} failed in {duration:.2f}s"
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


def preview_book_pdf(pdf_bytes: bytes, filename: str) -> BookPdfPreview:
    """Parse PDF metadata for preview before upload confirmation.

    Opens the PDF from bytes in memory, extracts title/author from PDF metadata,
    and returns a preview with page count.

    Args:
        pdf_bytes: Raw PDF file content
        filename: Original filename

    Returns:
        BookPdfPreview with extracted metadata

    Raises:
        ValueError: If the PDF is encrypted or has no extractable text
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    if doc.is_encrypted:
        doc.close()
        raise ValueError("PDF is password-protected and cannot be processed")

    # Check for extractable text (sample first few pages)
    has_text = False
    for page_num in range(min(3, doc.page_count)):
        if doc[page_num].get_text().strip():
            has_text = True
            break

    if not has_text:
        doc.close()
        raise ValueError("PDF has no extractable text (may be scanned/image-only)")

    metadata = doc.metadata or {}
    title = metadata.get("title", "").strip() or Path(filename).stem
    author = metadata.get("author", "").strip() or None
    page_count = doc.page_count

    doc.close()

    return BookPdfPreview(
        title=title,
        author=author,
        page_count=page_count,
        filename=filename,
    )


async def upload_book_pdf(
    db: AsyncSession,
    knowledge_source_id: uuid.UUID,
    pdf_bytes: bytes,
    filename: str,
    title: str,
    author: str | None,
) -> tuple[str, bool]:
    """Save a PDF to the vault and scaffold notes.

    Writes the PDF to /vault/Books/{title}/{filename} and scaffolds a Notes.md
    file if one doesn't exist. Does NOT create a Document record or run ingestion —
    those are handled by ingest_pdf_document() separately.

    Args:
        db: Database session
        knowledge_source_id: Parent knowledge source ID
        pdf_bytes: Raw PDF content
        filename: Original PDF filename
        title: User-edited book title (used as folder name)
        author: User-edited author (used in Notes.md frontmatter)

    Returns:
        Tuple of (relative_path, whether Notes.md was created)

    Raises:
        ValueError: If a document already exists at this path
    """
    # Sanitize the title for use as a folder name
    safe_title = title.strip().replace("/", "-").replace("\\", "-")
    book_dir = Path(VAULT_MOUNT_PATH) / BOOKS_DIR / safe_title
    pdf_path = book_dir / filename
    relative_path = f"{BOOKS_DIR}/{safe_title}/{filename}"

    # Check for duplicate
    existing = await Document.get_by_relative_path(db, knowledge_source_id, relative_path)
    if existing:
        raise ValueError(f"A document already exists at {relative_path}")

    # Create directory and write PDF
    book_dir.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(pdf_bytes)
    logger.info(f"Saved PDF to {pdf_path}")

    # Scaffold Notes.md if it doesn't exist
    notes_path = book_dir / "Notes.md"
    notes_created = False
    if not notes_path.exists():
        frontmatter_lines = [
            "---",
            f'title: "{safe_title}"',
            "type: book",
        ]
        if author:
            frontmatter_lines.append(f'author: "{author}"')
        frontmatter_lines.extend(["---", "", f"# {safe_title}", "", ""])

        notes_path.write_text("\n".join(frontmatter_lines), encoding="utf-8")
        notes_created = True
        logger.info(f"Scaffolded Notes.md at {notes_path}")

    return relative_path, notes_created

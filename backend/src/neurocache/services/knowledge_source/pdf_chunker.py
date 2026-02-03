"""PDF-specific chunking logic for book content."""

import logging

from neurocache.schemas.knowledge_source.document_chunk import ChunkData
from neurocache.schemas.knowledge_source.pdf import PageContent

logger = logging.getLogger(__name__)

# PDF chunking config (slightly larger than markdown for book content)
PDF_TARGET_CHUNK_SIZE = 1800  # target characters per chunk
PDF_MAX_CHUNK_SIZE = 2500  # ceiling - never exceed this
PDF_CHUNK_OVERLAP = 250  # characters of overlap between chunks
PDF_MIN_CHUNK_SIZE = 400  # avoid creating orphan chunks smaller than this


def _split_text_with_overlap(
    text: str,
    max_size: int = PDF_MAX_CHUNK_SIZE,
    overlap: int = PDF_CHUNK_OVERLAP,
    min_size: int = PDF_MIN_CHUNK_SIZE,
) -> list[str]:
    """Split text into chunks on paragraph breaks with overlap.

    Args:
        text: Text to split
        max_size: Maximum characters per chunk
        overlap: Characters of overlap between chunks
        min_size: Minimum chunk size

    Returns:
        List of text chunks
    """
    if len(text) <= max_size:
        return [text] if text.strip() else []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + max_size
        if end >= len(text):
            final_chunk = text[start:].strip()
            if final_chunk:
                # Merge small final chunks with previous
                if len(final_chunk) < min_size and chunks:
                    chunks[-1] = chunks[-1] + "\n\n" + final_chunk
                else:
                    chunks.append(final_chunk)
            break

        # Try to find a paragraph break near the end
        chunk = text[start:end]
        last_paragraph = chunk.rfind("\n\n")

        if last_paragraph > max_size // 2:
            end = start + last_paragraph + 2

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(chunk_text)

        start = end - overlap

    return chunks


def chunk_pdf_pages(pages: list[PageContent]) -> list[ChunkData]:
    """Chunk PDF pages respecting chapter boundaries.

    Strategy:
    1. Group pages by chapter
    2. Concatenate text within each chapter
    3. Split on paragraph breaks within chapters
    4. Preserve page number and chapter metadata

    Args:
        pages: List of PageContent from PDF extraction

    Returns:
        List of ChunkData with page_number and chapter metadata
    """
    if not pages:
        return []

    # Group pages by chapter
    chapter_groups: dict[str | None, list[PageContent]] = {}
    for page in pages:
        chapter = page.chapter
        if chapter not in chapter_groups:
            chapter_groups[chapter] = []
        chapter_groups[chapter].append(page)

    chunks: list[ChunkData] = []

    # Process each chapter group
    for chapter, chapter_pages in chapter_groups.items():
        # Track page boundaries for proper metadata
        page_texts: list[tuple[int | None, str]] = []
        for page in chapter_pages:
            if page.text.strip():
                page_texts.append((page.page_number, page.text))

        if not page_texts:
            continue

        # Concatenate all text in chapter with page markers
        combined_text = ""
        page_starts: list[tuple[int | None, int]] = []  # (page_number, char_offset)

        for page_num, text in page_texts:
            page_starts.append((page_num, len(combined_text)))
            combined_text += text + "\n\n"

        combined_text = combined_text.strip()

        # Split the combined text
        text_chunks = _split_text_with_overlap(combined_text)

        # Assign page numbers to chunks based on their position
        for chunk_text in text_chunks:
            # Find which page this chunk starts on
            chunk_start = combined_text.find(chunk_text)
            chunk_page: int | None = page_starts[0][0]  # Default to first page

            for pn, offset in page_starts:
                if offset <= chunk_start:
                    chunk_page = pn
                else:
                    break

            chunks.append(
                ChunkData(
                    content=chunk_text,
                    page_number=chunk_page,
                    chapter=chapter,
                )
            )

    # Final pass: merge orphan chunks that are too small
    merged_chunks: list[ChunkData] = []
    for chunk in chunks:
        if merged_chunks and len(chunk.content) < PDF_MIN_CHUNK_SIZE:
            # Merge with previous chunk, keep earlier chunk's metadata
            prev = merged_chunks[-1]
            merged_chunks[-1] = ChunkData(
                content=prev.content + "\n\n" + chunk.content,
                page_number=prev.page_number,
                chapter=prev.chapter,
            )
        else:
            merged_chunks.append(chunk)

    logger.info(f"Chunked PDF into {len(merged_chunks)} chunks from {len(pages)} pages")

    return merged_chunks

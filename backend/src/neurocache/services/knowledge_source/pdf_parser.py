"""PDF parsing utilities for extracting text and table of contents."""

import logging
from pathlib import Path

import pymupdf

from neurocache.schemas.knowledge_source.pdf import PageContent, TOCEntry

logger = logging.getLogger(__name__)


def extract_toc(doc: pymupdf.Document) -> list[TOCEntry]:
    """Parse PDF bookmarks/outline into TOC entries.

    Args:
        doc: PyMuPDF document object

    Returns:
        List of TOCEntry objects representing the document outline
    """
    toc_entries: list[TOCEntry] = []

    try:
        toc = doc.get_toc()  # Returns list of [level, title, page_number]
        for entry in toc:
            if len(entry) >= 3:
                level, title, page = entry[0], entry[1], entry[2]
                toc_entries.append(TOCEntry(level=level, title=str(title), page=page))
    except Exception:
        logger.warning("Failed to extract TOC from PDF")

    return toc_entries


def get_chapter_for_page(toc: list[TOCEntry], page_number: int | None) -> str | None:
    """Look up the chapter title for a given page number.

    Finds the most recent top-level chapter (level 1) that starts
    at or before the given page.

    Args:
        toc: List of TOC entries
        page_number: Printed page number to look up, or None for front matter

    Returns:
        Chapter title or None if no TOC or page is before first chapter
    """
    if not toc or page_number is None:
        return None

    # Filter to top-level chapters only (level 1)
    chapters = [entry for entry in toc if entry.level == 1]

    if not chapters:
        return None

    # Find the last chapter that starts at or before this page
    current_chapter: str | None = None
    for chapter in chapters:
        if chapter.page <= page_number:
            current_chapter = chapter.title
        else:
            break

    return current_chapter


def extract_pdf_content(file_path: Path) -> list[PageContent]:
    """Extract text content from all pages of a PDF.

    Args:
        file_path: Path to the PDF file

    Returns:
        List of PageContent objects, one per page

    Raises:
        ValueError: If PDF is password-protected or has no extractable text
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        doc = pymupdf.open(file_path)  # type: ignore[no-untyped-call]
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {e}") from e

    # Check for password protection
    if doc.is_encrypted:
        doc.close()  # type: ignore[no-untyped-call]
        raise ValueError(f"PDF is password-protected: {file_path}")

    # Extract TOC for chapter lookup
    toc = extract_toc(doc)

    pages: list[PageContent] = []
    total_text_length = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()  # type: ignore[no-untyped-call]

        # Try to get the printed page label (e.g., "84", "xii")
        # Only use numeric labels; front matter (Roman numerals, etc.) gets None
        page_label = page.get_label()  # type: ignore[no-untyped-call]
        page_number: int | None = None
        if page_label:
            try:
                page_number = int(page_label)
            except ValueError:
                # Non-numeric label (Roman numerals, etc.) - front matter
                pass

        # Look up chapter using display page number (skip for front matter)
        chapter = get_chapter_for_page(toc, page_number) if page_number else None

        pages.append(
            PageContent(
                page_number=page_number,
                text=text.strip(),
                chapter=chapter,
            )
        )
        total_text_length += len(text)

    doc.close()  # type: ignore[no-untyped-call]

    # Warn if PDF appears to be scanned (no text extracted)
    if total_text_length < 100 and len(pages) > 0:
        raise ValueError(
            f"PDF appears to be scanned with no extractable text: {file_path}. OCR is not currently supported."
        )

    logger.info(f"Extracted {len(pages)} pages from PDF, TOC has {len(toc)} entries")

    return pages

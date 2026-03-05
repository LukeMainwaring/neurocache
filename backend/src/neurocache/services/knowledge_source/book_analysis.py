"""Book analysis service: LLM-powered analysis of uploaded PDF books.

Extracts condensed content from a PDF, runs it through the book analysis agent
to generate tags, summary, and key concepts, then writes the results into Notes.md.
"""

import asyncio
import logging
import re
from pathlib import Path

import pymupdf

from neurocache.schemas.knowledge_source.book_analysis import BookAnalysis
from neurocache.schemas.knowledge_source.pdf import TOCEntry
from neurocache.services.knowledge_source.pdf_parser import extract_toc

logger = logging.getLogger(__name__)

# ~1.5M chars ≈ 375k tokens, fitting comfortably in gpt-5-mini's 400k context window
MAX_CONTENT_CHARS = 1_500_000
# Number of pages to include in the sampled fallback
FIRST_N_PAGES = 10

# Pattern to detect YAML frontmatter at the start of a file
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.DOTALL)


def _format_toc(toc: list[TOCEntry]) -> str:
    """Format TOC entries as an indented outline."""
    lines = []
    for entry in toc:
        indent = "  " * (entry.level - 1)
        lines.append(f"{indent}- {entry.title} (p. {entry.page})")
    return "\n".join(lines)


def _get_chapter_start_pages(toc: list[TOCEntry]) -> list[int]:
    """Get 0-indexed page numbers for the start of each top-level chapter."""
    return [entry.page - 1 for entry in toc if entry.level == 1]


def _extract_all_page_text(doc: pymupdf.Document) -> list[tuple[int, str]]:
    """Extract text from all pages, returning (1-indexed page number, text) pairs."""
    pages = []
    for i in range(len(doc)):
        text = doc[i].get_text().strip()
        if text:
            pages.append((i + 1, text))
    return pages


def prepare_analysis_content(pdf_path: Path) -> str:
    """Build book content for LLM analysis.

    Sends full text when it fits in context (~1.5M chars). Falls back to a sampled
    approach (TOC + first 10 pages + chapter openings) for very long books.
    """
    with pymupdf.open(pdf_path) as doc:
        toc = extract_toc(doc)
        all_pages = _extract_all_page_text(doc)

    sections: list[str] = []

    # Section 1: TOC (always included if available)
    if toc:
        sections.append(f"## Table of Contents\n\n{_format_toc(toc)}")

    # Calculate total text size
    total_chars = sum(len(text) for _, text in all_pages)

    if total_chars <= MAX_CONTENT_CHARS:
        # Full text fits — send everything
        page_texts = [f"[Page {num}]\n{text}" for num, text in all_pages]
        sections.append("## Book Content\n\n" + "\n\n".join(page_texts))
    else:
        # Sampled fallback for very long books
        logger.info(f"Book text ({total_chars} chars) exceeds budget ({MAX_CONTENT_CHARS}), using sampled approach")
        budget = MAX_CONTENT_CHARS

        # First N pages
        first_pages = []
        for num, text in all_pages[:FIRST_N_PAGES]:
            entry = f"[Page {num}]\n{text}"
            if len(entry) > budget:
                break
            first_pages.append(entry)
            budget -= len(entry)

        if first_pages:
            sections.append("## Opening Pages\n\n" + "\n\n".join(first_pages))

        # First page of each chapter (skip already-covered pages)
        if toc and budget > 0:
            chapter_pages = _get_chapter_start_pages(toc)
            covered_page_nums = {num for num, _ in all_pages[:FIRST_N_PAGES]}
            page_text_by_num = {num: text for num, text in all_pages}

            chapter_texts = []
            for page_idx in chapter_pages:
                page_num = page_idx + 1  # Convert to 1-indexed
                if page_num in covered_page_nums or page_num not in page_text_by_num:
                    continue
                text = page_text_by_num[page_num]
                chapter_title = next(
                    (e.title for e in toc if e.level == 1 and e.page - 1 == page_idx),
                    f"Page {page_num}",
                )
                entry = f"[{chapter_title}]\n{text}"
                if len(entry) > budget:
                    break
                chapter_texts.append(entry)
                budget -= len(entry)

            if chapter_texts:
                sections.append("## Chapter Openings\n\n" + "\n\n".join(chapter_texts))

    return "\n\n---\n\n".join(sections)


async def analyze_book(pdf_path: Path) -> BookAnalysis | None:
    """Run LLM analysis on a book PDF.

    Returns None if analysis fails (graceful degradation).
    """
    from neurocache.agents.book_analysis_agent import book_analysis_agent

    try:
        content = await asyncio.to_thread(prepare_analysis_content, pdf_path)
        if not content.strip():
            logger.warning(f"No content extracted from {pdf_path} for analysis")
            return None

        result = await book_analysis_agent.run(content)
        logger.info(f"Book analysis complete for {pdf_path}: {len(result.output.tags)} tags generated")
        return result.output

    except Exception:
        logger.exception(f"Book analysis failed for {pdf_path}, continuing without analysis")
        return None


_HUMAN_SECTIONS = """\
## Highlights & Annotations

_Add your favorite quotes and reflections here._

> "A memorable quote from the book that captures a key insight."

Your reflection: How does this connect to your own thinking or experience?

## How This Changed My Thinking

_What ideas will you carry forward? How does this connect to other things you've read or thought about? \
What actions might you take based on these ideas?_

## Connections

_Link to related notes in your vault._

- [[Related Note]] - How this book connects to other ideas
"""


def update_notes_with_analysis(notes_path: Path, analysis: BookAnalysis) -> None:
    """Write analysis results into an existing Notes.md file.

    Updates frontmatter with tags, appends AI-generated Summary and Key Concepts,
    then adds human-in-the-loop sections for personal reflection.
    """
    content = notes_path.read_text(encoding="utf-8")

    # 1. Update frontmatter: add tags in YAML inline list format for Obsidian
    tags_str = ", ".join(analysis.tags)
    fm_match = FRONTMATTER_PATTERN.match(content)
    if fm_match:
        fm_block = fm_match.group(0)
        lines = fm_block.rstrip().split("\n")
        # Insert tags before the closing --- (last line)
        lines.insert(-1, f"tags: [{tags_str}]")
        new_fm = "\n".join(lines) + "\n"
        content = new_fm + content[fm_match.end() :]

    # 2. Build AI-generated sections
    sections: list[str] = []
    sections.append(f"## Summary\n\n{analysis.summary}")

    concepts_parts: list[str] = []
    for kc in analysis.key_concepts:
        concept_items = "\n".join(f"- {c}" for c in kc.concepts)
        concepts_parts.append(f"### {kc.heading}\n\n{concept_items}")
    sections.append("## Key Concepts\n\n" + "\n\n".join(concepts_parts))

    # 3. Append AI sections + human-in-the-loop sections
    content = content.rstrip() + "\n\n" + "\n\n".join(sections) + "\n\n" + _HUMAN_SECTIONS

    notes_path.write_text(content, encoding="utf-8")
    logger.info(f"Updated {notes_path} with analysis (tags: {tags_str})")

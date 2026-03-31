"""Knowledge base search tool for Pydantic AI agents.

Provides the ``search_knowledge_base`` tool that lets agents query the user's
personal knowledge base on demand, along with helper functions for formatting
retrieved chunks into context strings and source metadata.
"""

import logging
from pathlib import Path
from urllib.parse import quote

from pydantic_ai import RunContext

from neurocache.agents.deps import AgentDeps
from neurocache.core.config import get_settings
from neurocache.models.document_chunk import DocumentChunk
from neurocache.schemas.knowledge_source.document import ContentType
from neurocache.services.knowledge_source.retrieval import search_hybrid_for_user
from neurocache.utils.message_serialization import RAGSource

logger = logging.getLogger(__name__)

config = get_settings()

# ============================================================================
# RAG Context Formatting (moved from chat_agent.py)
# ============================================================================


def build_obsidian_url(file_path: str) -> str:
    """Build an obsidian://open URI for a file in the vault.

    The vault name is derived from the vault directory name on disk (which is
    what Obsidian uses), not the app's display name. Markdown files have their
    ``.md`` extension stripped per Obsidian's URI convention.
    """
    vault_path = config.OBSIDIAN_VAULT_PATH
    vault_name = Path(vault_path).name if vault_path else config.OBSIDIAN_VAULT_NAME
    if file_path.endswith(".md"):
        file_path = file_path[:-3]
    return f"obsidian://open?vault={quote(vault_name, safe='')}&file={quote(file_path, safe='')}"


def _content_type_label(content_type: str | None) -> str:
    """Return a human-readable label for a content type."""
    labels: dict[str, str] = {
        ContentType.PERSONAL_NOTE.value: "Personal Note",
        ContentType.BOOK_NOTE.value: "Book Note",
        ContentType.BOOK_SOURCE.value: "Book Source",
        ContentType.ARTICLE.value: "Article",
    }
    return labels.get(content_type, "Note") if content_type else "Note"


def format_rag_context(
    relevant_chunks: list[tuple[DocumentChunk, float]],
    start_index: int = 1,
) -> tuple[str | None, list[RAGSource]]:
    """Format retrieved chunks into numbered context for the prompt.

    Reconstructs attribution prefixes from chunk metadata and document path
    (the chunk content itself is stored without prefixes for clean embeddings).
    Each source is numbered for inline citation (e.g., [1], [2]) by the agent.

    Args:
        relevant_chunks: List of (chunk, similarity) tuples from retrieval
        start_index: Starting source number (supports consecutive numbering
            across multiple search_knowledge_base calls in one turn)

    Returns:
        Tuple of (formatted_context, sources_metadata)
        - formatted_context: String for the prompt, or None if no relevant chunks
        - sources_metadata: List of source info dicts for the frontend
    """
    if not relevant_chunks:
        return None, []

    context_parts = []
    sources: list[RAGSource] = []

    for source_number, (chunk, similarity) in enumerate(relevant_chunks, start=start_index):
        doc = chunk.document
        source_path = doc.relative_path if doc else "Unknown"
        content_type = doc.content_type if doc else None
        doc_metadata = doc.doc_metadata if doc else None
        chunk_meta = chunk.chunk_metadata or {}

        # Build attribution prefix with content type
        type_label = _content_type_label(content_type)
        prefix = f"[Source: {source_path} ({type_label})]"

        # Add author for book notes and book sources
        if content_type in (ContentType.BOOK_NOTE.value, ContentType.BOOK_SOURCE.value) and doc_metadata:
            author = doc_metadata.get("author")
            if author:
                prefix += f"\n[Author: {author}]"

        # Add page number for book sources (PDFs)
        page_number = chunk_meta.get("page_number")
        if page_number:
            prefix += f"\n[Page: {page_number}]"

        # Add chapter for book sources (PDFs)
        chapter = chunk_meta.get("chapter")
        if chapter:
            prefix += f"\n[Chapter: {chapter}]"

        # Add section header if available (markdown documents)
        section_header = chunk_meta.get("section_header")
        if section_header:
            prefix += f"\n[Section: {section_header}]"

        context_parts.append(f"[{source_number}] {prefix}\n\n{chunk.content}")

        # Build source metadata for frontend
        source: RAGSource = {
            "path": source_path,
            "similarity": float(similarity),
            "content": chunk.content,
            "source_number": source_number,
            "obsidian_url": build_obsidian_url(source_path),
        }
        if content_type:
            source["content_type"] = content_type
        if section_header:
            source["section_header"] = section_header
        if page_number:
            source["page_number"] = page_number
        if chapter:
            source["chapter"] = chapter
        if content_type in (ContentType.BOOK_NOTE.value, ContentType.BOOK_SOURCE.value) and doc_metadata:
            if doc_metadata.get("author"):
                source["author"] = doc_metadata["author"]
        sources.append(source)

    return "\n\n---\n\n".join(context_parts), sources


# ============================================================================
# Knowledge Base Tool
# ============================================================================


async def search_knowledge_base(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search the user's personal knowledge base for relevant notes, highlights, and documents.

    Use this tool when the user's message relates to topics they may have notes on,
    references their reading or research, or when drawing connections across their
    knowledge would be valuable.

    Args:
        query: Search query. Use specific key terms, concepts, or names
               rather than vague phrases. Rephrase the user's question into
               effective search terms.
    """
    try:
        chunks = await search_hybrid_for_user(ctx.deps.db, ctx.deps.openai_client, query, ctx.deps.user.id)
        if not chunks:
            return "No relevant results found in the knowledge base."

        # Offset source numbering for consecutive citations across multiple searches
        start_index = len(ctx.deps.rag_sources) + 1
        formatted_context, sources = format_rag_context(chunks, start_index=start_index)
        ctx.deps.rag_sources.extend(sources)
        return formatted_context or "No relevant results found in the knowledge base."
    except Exception:
        logger.exception("Error searching knowledge base")
        return "An error occurred while searching the knowledge base."

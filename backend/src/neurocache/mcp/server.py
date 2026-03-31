"""FastMCP server exposing the Neurocache knowledge base as MCP tools.

Provides search, document reading, and browsing capabilities for use
with Claude Desktop, Claude Code, Cursor, or any MCP-compatible client.

Neurocache backend imports are deferred to inside tool functions (not at
module level) because module-level imports trigger side effects like
AsyncOpenAI() initialization and get_settings() validation that require
environment variables which may not be available until the MCP process
has fully started.
"""

import logging
from typing import Any

from fastmcp import Context, FastMCP

from neurocache.mcp.deps import mcp_lifespan

logger = logging.getLogger(__name__)

VALID_CONTENT_TYPES = {"personal_note", "book_note", "book_source", "article", "chat_insight"}

CONTENT_TYPE_LABELS: dict[str, str] = {
    "personal_note": "Personal Notes",
    "book_note": "Book Notes",
    "book_source": "Book Sources",
    "article": "Articles",
    "chat_insight": "Chat Insights",
}

mcp = FastMCP(
    "Neurocache",
    instructions=(
        "Neurocache is a personal knowledge base containing Obsidian notes, "
        "book notes, book sources (PDFs), and curated articles. "
        "Use search_knowledge_base to find relevant information by topic, concept, "
        "author name, or book title. Use list_documents to browse what's available. "
        "Use get_document to read a specific document's full content. "
        "Use save_to_knowledge_base to save insights, decisions, or knowledge "
        "from the current conversation into the vault for future retrieval."
    ),
    lifespan=mcp_lifespan,
)


def _get_lifespan(ctx: Context) -> dict[str, Any]:
    """Extract lifespan context with user_id and openai_client.

    Raises ValueError if NEUROCACHE_USER_ID was not configured at startup.
    """
    lifespan = ctx.lifespan_context
    if not lifespan.get("user_id"):
        raise ValueError(
            "MCP server is not configured. Set NEUROCACHE_USER_ID in your "
            ".env file or environment to enable knowledge base access."
        )
    return lifespan


def _parse_content_type(content_type: str | None) -> list[Any] | None:
    """Parse and validate an optional content_type filter string."""
    if not content_type:
        return None
    if content_type not in VALID_CONTENT_TYPES:
        valid = ", ".join(sorted(VALID_CONTENT_TYPES))
        raise ValueError(f"Invalid content_type '{content_type}'. Must be one of: {valid}")
    from neurocache.schemas.knowledge_source.document import ContentType

    return [ContentType(content_type)]


# ============================================================================
# Tools
# ============================================================================


@mcp.tool()
async def search_knowledge_base(
    query: str,
    ctx: Context,
    content_type: str | None = None,
    top_k: int = 10,
) -> str:
    """Search the personal knowledge base using hybrid semantic + keyword search.

    Returns the most relevant passages from notes, book highlights, articles,
    and PDFs, with numbered source attribution. Use specific key terms, concepts,
    author names, or book titles for best results.

    Args:
        query: Search query. Use specific terms rather than vague phrases.
        content_type: Optional filter. One of: personal_note, book_note, book_source, article.
        top_k: Maximum results to return (default 10, max 20).
    """
    from neurocache.agents.tools.knowledge_base_tools import format_rag_context
    from neurocache.dependencies.db import get_async_sqlalchemy_session
    from neurocache.services.knowledge_source.retrieval import search_hybrid_for_user

    lifespan = _get_lifespan(ctx)
    user_id = lifespan["user_id"]
    openai_client = lifespan["openai_client"]

    top_k = max(1, min(top_k, 20))
    content_types = _parse_content_type(content_type)

    async with get_async_sqlalchemy_session() as db:
        chunks = await search_hybrid_for_user(
            db, openai_client, query, user_id, top_k=top_k, content_types=content_types
        )

        if not chunks:
            return f"No relevant results found in the knowledge base for: '{query}'"

        formatted, _sources = format_rag_context(chunks)
        return formatted or f"No relevant results found in the knowledge base for: '{query}'"


@mcp.tool()
async def get_document(path: str, ctx: Context) -> str:
    """Read the full content of a document from the knowledge base by its path.

    Use this after search_knowledge_base returns relevant snippets and you need
    the complete document. The path should match a relative_path from search results
    (e.g., "Brain Dump.md", "Books/Deep Work/Notes.md").

    Args:
        path: The document's relative path as shown in search results.
    """
    from sqlalchemy import select

    from neurocache.dependencies.db import get_async_sqlalchemy_session
    from neurocache.models.document import Document
    from neurocache.models.document_chunk import DocumentChunk
    from neurocache.models.knowledge_source import KnowledgeSource
    from neurocache.schemas.knowledge_source.document import DocumentStatus

    lifespan = _get_lifespan(ctx)
    user_id = lifespan["user_id"]

    async with get_async_sqlalchemy_session() as db:
        # Search across all user's knowledge sources for the document
        sources = await KnowledgeSource.list_for_user(db, user_id)
        document: Document | None = None
        for source in sources:
            document = await Document.get_by_relative_path(db, source.id, path)
            if document:
                break

        if not document:
            return (
                f"No document found with path: '{path}'. Use list_documents to see available documents and their paths."
            )

        if document.status != DocumentStatus.INDEXED:
            return (
                f"Document '{path}' exists but has not been indexed (status: {document.status}). "
                "Re-sync the knowledge source to index it."
            )

        # Load all chunks ordered by position
        max_chunks = 50
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
            .limit(max_chunks)
        )
        result = await db.execute(stmt)
        chunks = list(result.scalars().all())

        if not chunks:
            return f"Document '{path}' has no indexed content."

        # Build header with metadata
        content_type_label = CONTENT_TYPE_LABELS.get(document.content_type, "Note")
        header_parts = [f"# {document.title or path}", f"Type: {content_type_label}"]

        doc_meta = document.doc_metadata or {}
        if doc_meta.get("author"):
            header_parts.append(f"Author: {doc_meta['author']}")

        header_parts.append(f"Chunks: {document.chunk_count}")

        if document.chunk_count > max_chunks:
            header_parts.append(f"(showing first {max_chunks} of {document.chunk_count} chunks)")

        header = "\n".join(header_parts)
        body = "\n\n".join(chunk.content for chunk in chunks)

        return f"{header}\n\n---\n\n{body}"


@mcp.tool()
async def list_documents(ctx: Context, content_type: str | None = None) -> str:
    """List all indexed documents in the knowledge base.

    Returns document paths, titles, content types, and metadata. Use this to
    discover what's available before searching or reading specific documents.

    Args:
        content_type: Optional filter. One of: personal_note, book_note, book_source, article.
    """
    from neurocache.dependencies.db import get_async_sqlalchemy_session
    from neurocache.models.document import Document
    from neurocache.models.knowledge_source import KnowledgeSource
    from neurocache.schemas.knowledge_source.document import DocumentStatus

    lifespan = _get_lifespan(ctx)
    user_id = lifespan["user_id"]

    content_type_filter = _parse_content_type(content_type)

    async with get_async_sqlalchemy_session() as db:
        sources = await KnowledgeSource.list_for_user(db, user_id)

        all_docs: list[Document] = []
        for source in sources:
            docs = await Document.get_all_by_source(db, source.id)
            all_docs.extend(docs)

        # Filter to indexed documents only
        indexed = [d for d in all_docs if d.status == DocumentStatus.INDEXED]

        # Apply content type filter
        if content_type_filter:
            filter_values = {ct.value for ct in content_type_filter}
            indexed = [d for d in indexed if d.content_type in filter_values]

        if not indexed:
            filter_msg = f" with content_type='{content_type}'" if content_type else ""
            return f"No indexed documents found{filter_msg}."

        # Group by content type
        grouped: dict[str, list[Document]] = {}
        for doc in indexed:
            grouped.setdefault(doc.content_type, []).append(doc)

        # Sort each group by path
        for docs in grouped.values():
            docs.sort(key=lambda d: d.relative_path)

        # Format output
        sections: list[str] = []
        for ct_value, ct_label in CONTENT_TYPE_LABELS.items():
            docs = grouped.get(ct_value, [])
            if not docs:
                continue

            lines = [f"## {ct_label} ({len(docs)} documents)"]
            for doc in docs:
                meta_parts: list[str] = []
                doc_meta = doc.doc_metadata or {}
                if doc_meta.get("author"):
                    meta_parts.append(f"Author: {doc_meta['author']}")
                meta_parts.append(f"{doc.chunk_count} chunks")

                meta_str = " — ".join(meta_parts)
                title = doc.title or doc.relative_path
                if title != doc.relative_path:
                    lines.append(f"- {doc.relative_path} ({title}) [{meta_str}]")
                else:
                    lines.append(f"- {doc.relative_path} [{meta_str}]")

            sections.append("\n".join(lines))

        total = len(indexed)
        return "\n\n".join(sections) + f"\n\nTotal: {total} indexed documents"


@mcp.tool()
async def save_to_knowledge_base(
    title: str,
    content: str,
    ctx: Context,
    tags: list[str] | None = None,
) -> str:
    """Save insights, decisions, or knowledge to the Obsidian vault.

    Use this when the user asks to save something from the conversation to their
    knowledge base, or when you identify valuable insights worth preserving.
    The note will be written to the vault and indexed for future retrieval.

    Write the content in Obsidian-native markdown — use bullet points, bold,
    headers (##), and [[wiki-links]] to existing notes where relevant.

    Args:
        title: Concise, descriptive title for the note (3-8 words).
        content: Markdown body of the note. Write substantive, reference-friendly
            content — not a transcript, but distilled knowledge.
        tags: Optional list of lowercase-hyphenated tags (e.g., ["machine-learning", "architecture"]).
    """
    from neurocache.dependencies.db import get_async_sqlalchemy_session
    from neurocache.models.knowledge_source import KnowledgeSource
    from neurocache.services.extraction import compose_insight_markdown, write_and_ingest_note

    lifespan = _get_lifespan(ctx)
    user_id = lifespan["user_id"]
    openai_client = lifespan["openai_client"]

    async with get_async_sqlalchemy_session() as db:
        sources = await KnowledgeSource.list_for_user(db, user_id)
        if not sources:
            return "No knowledge source configured. Add one in the Neurocache settings first."

        knowledge_source_id = sources[0].id
        vault_path = sources[0].file_path
        if not vault_path:
            return "Knowledge source has no file path configured."
        full_content = compose_insight_markdown(title, content, tags)

        # No Extraction provenance record here — MCP has no thread context.
        # Notes saved via MCP are tracked only as Documents in the knowledge source.
        try:
            relative_path, obsidian_url = await write_and_ingest_note(
                db, openai_client, knowledge_source_id, title, full_content, vault_path=vault_path
            )
        except Exception:
            logger.exception("Failed to save note to knowledge base")
            return f"Failed to save note '{title}' to the knowledge base. Check the server logs for details."

        return f"Saved and indexed: {relative_path}\nOpen in Obsidian: {obsidian_url}"

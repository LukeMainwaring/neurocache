"""Search vector builder for hybrid full-text search.

Computes weighted tsvector values for document chunks by combining chunk
content with parent document metadata (title, author, tags, section headers).
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def populate_search_vectors(db: AsyncSession, document_id: uuid.UUID) -> None:
    """Compute and store search vectors for all chunks of a document.

    Builds a weighted tsvector per chunk:
      - Weight A: document title, author (highest priority for keyword lookup)
      - Weight B: tags, section_header, chapter (structural metadata)
      - Weight C: chunk content (body text)

    Uses 'english' config for most fields (stemming improves natural language
    matching; proper nouns are unaffected) and 'simple' config for tags
    (preserves exact tag forms with hyphens replaced by spaces).

    Args:
        db: Database session (must be flushed so chunks exist)
        document_id: The document whose chunks should be updated
    """
    await db.execute(
        text("""
            UPDATE document_chunks dc
            SET search_vector = (
                setweight(to_tsvector('english', coalesce(d.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(d.doc_metadata->>'author', '')), 'A') ||
                setweight(to_tsvector('simple', replace(coalesce(d.doc_metadata->>'tags', ''), '-', ' ')), 'B') ||
                setweight(to_tsvector('english', coalesce(dc.chunk_metadata->>'section_header', '')), 'B') ||
                setweight(to_tsvector('english', coalesce(dc.chunk_metadata->>'chapter', '')), 'B') ||
                setweight(to_tsvector('english', dc.content), 'C')
            )
            FROM documents d
            WHERE dc.document_id = d.id
              AND dc.document_id = :doc_id
        """),
        {"doc_id": str(document_id)},
    )

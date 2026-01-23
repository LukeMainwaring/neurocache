"""Knowledge source management API endpoints.

This module provides REST API endpoints for knowledge source CRUD operations.
"""

import logging

from fastapi import APIRouter

from neurocache.core.config import get_settings
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.dependencies.openai import OpenAIClientDep
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.schemas.document import DocumentSchema
from neurocache.schemas.knowledge_source import (
    KnowledgeSourceCreateSchema,
    KnowledgeSourceListResponse,
    KnowledgeSourceSchema,
    KnowledgeSourceStatus,
    KnowledgeSourceType,
    KnowledgeSourceUpdateSchema,
)
from neurocache.services.ingestion import ingest_document
from neurocache.services.retrieval import search_similar_chunks
from neurocache.services.vault_validator import validate_obsidian_vault

logger = logging.getLogger(__name__)

config = get_settings()

knowledge_source_router = APIRouter(prefix="/knowledge-sources", tags=["knowledge-sources"])

# Using same demo user pattern as user.py
DEMO_USER_ID = "110771214372945994893"


@knowledge_source_router.get("")
async def list_knowledge_sources(
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceListResponse:
    """List all knowledge sources for the current user."""
    sources = await KnowledgeSource.list_for_user(db, DEMO_USER_ID)
    return KnowledgeSourceListResponse(sources=sources)


@knowledge_source_router.post("")
async def create_knowledge_source(
    source_data: KnowledgeSourceCreateSchema,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Create a new knowledge source and validate if it's an Obsidian vault."""
    source = await KnowledgeSource.create(db, DEMO_USER_ID, source_data)

    if source_data.source_type == KnowledgeSourceType.OBSIDIAN:
        is_valid, error_message = await validate_obsidian_vault()
        if is_valid:
            source = await KnowledgeSource.update_status(db, source.id, DEMO_USER_ID, KnowledgeSourceStatus.CONNECTED)
        else:
            source = await KnowledgeSource.update_status(
                db, source.id, DEMO_USER_ID, KnowledgeSourceStatus.ERROR, error_message
            )
    return source


@knowledge_source_router.get("/defaults")
async def get_knowledge_source_defaults() -> dict[str, dict[str, str | None]]:
    """Return default values for creating a knowledge source."""

    return {
        "obsidian": {
            "name": config.OBSIDIAN_VAULT_NAME,
            "file_path": config.OBSIDIAN_VAULT_PATH,
        }
    }


@knowledge_source_router.get("/{source_id}")
async def get_knowledge_source(
    source_id: str,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Get a single knowledge source by ID."""
    return await KnowledgeSource.get(db, source_id, DEMO_USER_ID)


@knowledge_source_router.patch("/{source_id}")
async def update_knowledge_source(
    source_id: str,
    source_data: KnowledgeSourceUpdateSchema,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Update a knowledge source."""
    return await KnowledgeSource.update(db, source_id, DEMO_USER_ID, source_data)


@knowledge_source_router.delete("/{source_id}")
async def delete_knowledge_source(
    source_id: str,
    db: AsyncPostgresSessionDep,
) -> None:
    """Delete a knowledge source."""
    await KnowledgeSource.delete(db, source_id, DEMO_USER_ID)


@knowledge_source_router.post("/{source_id}/ingest")
async def ingest_single_document(
    source_id: str,
    relative_path: str,
    db: AsyncPostgresSessionDep,
    openai_client: OpenAIClientDep,
) -> DocumentSchema:
    """Ingest a single document from a knowledge source.

    Args:
        source_id: The knowledge source ID
        relative_path: Path relative to knowledge source root (e.g., "TODO.md")
    """
    document = await ingest_document(db, openai_client, source_id, relative_path)
    return DocumentSchema.model_validate(document)


@knowledge_source_router.get("/{source_id}/search")
async def search_knowledge_source(
    source_id: str,
    query: str,
    db: AsyncPostgresSessionDep,
    openai_client: OpenAIClientDep,
    top_k: int = 5,
) -> list[dict[str, str | float | int]]:
    """Search for similar chunks within a knowledge source.

    Args:
        source_id: The knowledge source ID to search within
        query: The search query text
        top_k: Number of results to return (default 5)
    """
    results = await search_similar_chunks(db, openai_client, query, top_k, source_id)
    return [
        {
            "chunk_id": chunk.id,
            "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "similarity": round(similarity, 4),
            "chunk_index": chunk.chunk_index,
        }
        for chunk, similarity in results
    ]

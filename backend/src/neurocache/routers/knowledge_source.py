"""Knowledge source management API endpoints.

This module provides REST API endpoints for knowledge source CRUD operations.
"""

import logging
import uuid

from fastapi import APIRouter

from neurocache.core.config import get_settings
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.dependencies.openai import OpenAIClientDep
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.schemas.knowledge_source.document import BatchIngestResult, BookListResponse, DocumentSchema
from neurocache.schemas.knowledge_source.knowledge_source import (
    KnowledgeSourceCreateSchema,
    KnowledgeSourceDefaults,
    KnowledgeSourceListResponse,
    KnowledgeSourceSchema,
    KnowledgeSourceUpdateSchema,
    ObsidianDefaults,
)
from neurocache.services.knowledge_source import ingestion as ingestion_service
from neurocache.services.knowledge_source import knowledge_source as knowledge_source_service

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
    return await knowledge_source_service.create_and_validate(source_data, db)


@knowledge_source_router.get("/defaults")
async def get_knowledge_source_defaults() -> KnowledgeSourceDefaults:
    """Return default values for creating a knowledge source."""
    return KnowledgeSourceDefaults(
        obsidian=ObsidianDefaults(
            name=config.OBSIDIAN_VAULT_NAME,
            file_path=config.OBSIDIAN_VAULT_PATH,
        )
    )


@knowledge_source_router.get("/{source_id}")
async def get_knowledge_source(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Get a single knowledge source by ID."""
    return await KnowledgeSource.get(db, source_id, DEMO_USER_ID)


@knowledge_source_router.get("/{source_id}/books")
async def list_books(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
) -> BookListResponse:
    """List books grouped by subfolder for a knowledge source."""
    return await knowledge_source_service.list_books(source_id, db)


@knowledge_source_router.patch("/{source_id}")
async def update_knowledge_source(
    source_id: uuid.UUID,
    source_data: KnowledgeSourceUpdateSchema,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Update a knowledge source."""
    return await KnowledgeSource.update(db, source_id, DEMO_USER_ID, source_data)


@knowledge_source_router.delete("/{source_id}")
async def delete_knowledge_source(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
) -> None:
    """Delete a knowledge source."""
    await KnowledgeSource.delete(db, source_id, DEMO_USER_ID)


@knowledge_source_router.post("/{source_id}/retry")
async def retry_knowledge_source(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Re-validate an existing knowledge source connection."""
    return await knowledge_source_service.retry_validation(source_id, db)


@knowledge_source_router.post("/{source_id}/ingest")
async def ingest_document(
    source_id: uuid.UUID,
    relative_path: str,
    db: AsyncPostgresSessionDep,
    openai_client: OpenAIClientDep,
) -> DocumentSchema:
    """Ingest a single document from a knowledge source.

    Args:
        source_id: The knowledge source ID
        relative_path: Path relative to knowledge source root (e.g., "Brain Dump.md")
    """
    document = await ingestion_service.ingest_document(db, openai_client, source_id, relative_path)
    return DocumentSchema.model_validate(document)


@knowledge_source_router.post("/{source_id}/ingest-all")
async def ingest_all_documents(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
    openai_client: OpenAIClientDep,
    force_reindex: bool = False,
) -> BatchIngestResult:
    """Ingest all markdown documents from a knowledge source.

    Discovers all .md files in the vault (excluding system directories like .obsidian)
    and ingests them into the database with embeddings. Manages source lifecycle
    (status transitions, timestamps, stats).

    Args:
        source_id: The knowledge source ID
        force_reindex: If True, re-ingest documents even if already indexed
    """
    return await knowledge_source_service.sync_documents(source_id, db, openai_client, force_reindex)

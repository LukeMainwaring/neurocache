"""Knowledge source management API endpoints.

This module provides REST API endpoints for knowledge source CRUD operations.
"""

import logging

from fastapi import APIRouter

from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.schemas.knowledge_source import (
    KnowledgeSourceCreateSchema,
    KnowledgeSourceListResponse,
    KnowledgeSourceSchema,
    KnowledgeSourceUpdateSchema,
)

logger = logging.getLogger(__name__)

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
    """Create a new knowledge source."""
    return await KnowledgeSource.create(db, DEMO_USER_ID, source_data)


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

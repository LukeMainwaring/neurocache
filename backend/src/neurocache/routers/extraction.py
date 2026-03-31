"""Extraction router for conversation-to-knowledge pipeline.

Provides endpoints to preview, confirm, and check status of
knowledge extractions from chat conversations.
"""

import logging

from fastapi import APIRouter, HTTPException

from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.dependencies.openai import OpenAIClientDep
from neurocache.models.document import Document
from neurocache.models.extraction import Extraction
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.models.thread import Thread
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.extraction import (
    ExtractionConfirmRequest,
    ExtractionPreview,
    ExtractionPreviewRequest,
    ExtractionResponse,
    ExtractionStatusResponse,
    ExtractionSummary,
)
from neurocache.schemas.knowledge_source.knowledge_source import KnowledgeSourceSchema
from neurocache.services import extraction as extraction_service

logger = logging.getLogger(__name__)

extraction_router = APIRouter(prefix="/extractions", tags=["extractions"])

AGENT_TYPE = AgentType.CHAT.value


async def _get_user_knowledge_source(db: AsyncPostgresSessionDep, user_id: str) -> KnowledgeSourceSchema:
    """Get the user's knowledge source, raising 400 if none configured."""
    sources = await KnowledgeSource.list_for_user(db, user_id)
    if not sources:
        raise HTTPException(
            status_code=400,
            detail="No knowledge source configured. Add one in Settings.",
        )
    # Use the first (primary) knowledge source
    return sources[0]


@extraction_router.post("/preview")
async def preview_extraction(
    request: ExtractionPreviewRequest,
    user_id: AuthenticatedUser,
    db: AsyncPostgresSessionDep,
) -> ExtractionPreview:
    """Generate an extraction preview from a conversation.

    Runs the extraction agent to analyze the thread and produce
    a structured Obsidian note for user review.
    """
    # Validate thread ownership
    await Thread.get_for_user(db, request.thread_id, user_id, AGENT_TYPE)

    return await extraction_service.preview_extraction(
        db=db,
        thread_id=request.thread_id,
        agent_type=AGENT_TYPE,
        user_id=user_id,
    )


@extraction_router.post("/confirm")
async def confirm_extraction(
    request: ExtractionConfirmRequest,
    user_id: AuthenticatedUser,
    db: AsyncPostgresSessionDep,
    openai_client: OpenAIClientDep,
) -> ExtractionResponse:
    """Save an extraction to the vault.

    Writes the markdown file, runs ingestion (chunk, embed, index),
    and creates a provenance record.
    """
    # Validate thread ownership
    await Thread.get_for_user(db, request.thread_id, user_id, AGENT_TYPE)

    source = await _get_user_knowledge_source(db, user_id)

    return await extraction_service.save_extraction(
        db=db,
        openai_client=openai_client,
        knowledge_source_id=source.id,
        thread_id=request.thread_id,
        agent_type=AGENT_TYPE,
        title=request.title,
        content=request.content,
    )


@extraction_router.get("")
async def get_extraction_status(
    thread_id: str,
    user_id: AuthenticatedUser,
    db: AsyncPostgresSessionDep,
) -> ExtractionStatusResponse:
    """Check if a thread has been extracted."""
    # Validate thread ownership
    await Thread.get_for_user(db, thread_id, user_id, AGENT_TYPE)

    extractions = await Extraction.get_by_thread(db, thread_id, AGENT_TYPE)

    summaries: list[ExtractionSummary] = []
    for ext in extractions:
        doc = await db.get(Document, ext.document_id)
        summaries.append(
            ExtractionSummary(
                id=ext.id,
                document_id=ext.document_id,
                relative_path=doc.relative_path if doc else "unknown",
                created_at=ext.created_at,
            )
        )

    return ExtractionStatusResponse(extractions=summaries)

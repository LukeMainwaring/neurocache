"""Extraction router for conversation-to-knowledge pipeline.

Provides endpoints to preview, confirm, and check status of
knowledge extractions from chat conversations.
"""

from fastapi import APIRouter

from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.dependencies.openai import OpenAIClientDep
from neurocache.models.thread import Thread
from neurocache.schemas.agent_type import AgentType
from neurocache.schemas.extraction import (
    ExtractionConfirmRequest,
    ExtractionPreview,
    ExtractionPreviewRequest,
    ExtractionResponse,
    ExtractionStatusResponse,
)
from neurocache.services import extraction as extraction_service

extraction_router = APIRouter(prefix="/extractions", tags=["extractions"])

AGENT_TYPE = AgentType.CHAT.value


@extraction_router.post("/preview")
async def preview_extraction(
    request: ExtractionPreviewRequest,
    user_id: AuthenticatedUser,
    db: AsyncPostgresSessionDep,
) -> ExtractionPreview:
    """Generate an extraction preview from a conversation."""
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
    """Save an extraction to the vault."""
    await Thread.get_for_user(db, request.thread_id, user_id, AGENT_TYPE)
    knowledge_source_id = await extraction_service.get_user_knowledge_source_id(db, user_id)

    return await extraction_service.save_extraction(
        db=db,
        openai_client=openai_client,
        knowledge_source_id=knowledge_source_id,
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
    await Thread.get_for_user(db, thread_id, user_id, AGENT_TYPE)

    return await extraction_service.get_extraction_status(db, thread_id, AGENT_TYPE)

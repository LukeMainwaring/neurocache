"""Knowledge source management API endpoints.

This module provides REST API endpoints for knowledge source CRUD operations.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile

from neurocache.core.config import get_settings
from neurocache.dependencies.db import AsyncPostgresSessionDep, AsyncSessionMakerDep
from neurocache.dependencies.openai import OpenAIClientDep
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.schemas.knowledge_source.document import (
    BatchIngestResult,
    BookListResponse,
    BookPdfPreview,
    BookUploadResponse,
    DocumentSchema,
)
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


MAX_PDF_SIZE_MB = 50


@knowledge_source_router.post("/{source_id}/preview-book")
async def preview_book_pdf(
    source_id: uuid.UUID,
    file: UploadFile,
) -> BookPdfPreview:
    """Parse PDF metadata for preview before upload confirmation."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(pdf_bytes) > MAX_PDF_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_PDF_SIZE_MB}MB limit")

    try:
        return ingestion_service.preview_book_pdf(pdf_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@knowledge_source_router.post("/{source_id}/upload-book")
async def upload_book_pdf(
    source_id: uuid.UUID,
    file: UploadFile,
    title: str = Form(...),
    author: str | None = Form(default=None),
    *,
    db: AsyncPostgresSessionDep,
    session_maker: AsyncSessionMakerDep,
    openai_client: OpenAIClientDep,
    background_tasks: BackgroundTasks,
) -> BookUploadResponse:
    """Upload a PDF book, save to vault, and trigger background ingestion."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(pdf_bytes) > MAX_PDF_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_PDF_SIZE_MB}MB limit")

    try:
        relative_path, notes_created = await ingestion_service.upload_book_pdf(
            db, source_id, pdf_bytes, file.filename, title, author
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    # Trigger background ingestion with its own DB session
    async def _ingest_in_background() -> None:
        async with session_maker.new_async_session() as bg_db:
            try:
                await ingestion_service.ingest_pdf_document(bg_db, openai_client, source_id, relative_path)
            except Exception:
                logger.exception(f"Background ingestion failed for {relative_path}")

    background_tasks.add_task(_ingest_in_background)

    return BookUploadResponse(
        relative_path=relative_path,
        notes_created=notes_created,
    )

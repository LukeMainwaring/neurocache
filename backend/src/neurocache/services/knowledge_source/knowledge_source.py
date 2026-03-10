import logging
import uuid
from datetime import datetime, timezone

from openai import AsyncOpenAI

from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.models.document import Document
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.schemas.knowledge_source.document import (
    BatchIngestResult,
    BookDocumentSummary,
    BookListResponse,
    BookSchema,
    ContentType,
    DocumentStatus,
)
from neurocache.schemas.knowledge_source.knowledge_source import (
    KnowledgeSourceCreateSchema,
    KnowledgeSourceSchema,
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from neurocache.services.knowledge_source import ingestion as ingestion_service
from neurocache.services.knowledge_source.vault_validator import validate_obsidian_vault

logger = logging.getLogger(__name__)


DEMO_USER_ID = "110771214372945994893"


async def create_and_validate(
    source_data: KnowledgeSourceCreateSchema,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Create a new knowledge source and validate if it's an Obsidian vault."""
    source = await KnowledgeSource.create(db, DEMO_USER_ID, source_data)
    if source_data.source_type == KnowledgeSourceType.OBSIDIAN:
        source = await _validate_obsidian_source(db, source)
    return source


async def retry_validation(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
) -> KnowledgeSourceSchema:
    """Re-validate an existing knowledge source."""
    source = await KnowledgeSource.get(db, source_id, DEMO_USER_ID)
    if source.source_type == KnowledgeSourceType.OBSIDIAN:
        source = await _validate_obsidian_source(db, source)
    return source


async def sync_documents(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
    openai_client: AsyncOpenAI,
    force_reindex: bool = False,
) -> BatchIngestResult:
    """Sync all documents for a knowledge source with lifecycle management.

    Sets status to SYNCING, ingests all documents, then updates status
    to CONNECTED on success or ERROR on failure.
    """
    # Validate source exists and belongs to user
    source = await KnowledgeSource.get(db, source_id, DEMO_USER_ID)

    await KnowledgeSource.update_status(db, source.id, DEMO_USER_ID, KnowledgeSourceStatus.SYNCING)

    try:
        result = await ingestion_service.ingest_all_documents(db, openai_client, source_id, force_reindex)
        config = (source.config or {}) | {
            "documents_indexed": result.documents_created + result.documents_updated + result.documents_skipped,
            "documents_failed": result.documents_failed,
        }
        await KnowledgeSource.update_status(
            db,
            source.id,
            DEMO_USER_ID,
            KnowledgeSourceStatus.CONNECTED,
            config=config,
            last_synced_at=datetime.now(timezone.utc),
        )
        return result

    except Exception:
        await KnowledgeSource.update_status(
            db,
            source.id,
            DEMO_USER_ID,
            KnowledgeSourceStatus.ERROR,
            error_message="Sync failed unexpectedly",
        )
        raise


async def _validate_obsidian_source(
    db: AsyncPostgresSessionDep,
    source: KnowledgeSourceSchema,
) -> KnowledgeSourceSchema:
    """Validate an Obsidian vault source and update its status."""
    is_valid, error_message, file_count = await validate_obsidian_vault(
        user_file_path=source.file_path or "",
    )
    if is_valid:
        return await KnowledgeSource.update_status(
            db,
            source.id,
            DEMO_USER_ID,
            KnowledgeSourceStatus.CONNECTED,
            config={"file_count": file_count},
        )
    return await KnowledgeSource.update_status(
        db,
        source.id,
        DEMO_USER_ID,
        KnowledgeSourceStatus.ERROR,
        error_message,
    )


async def list_books(
    source_id: uuid.UUID,
    db: AsyncPostgresSessionDep,
) -> BookListResponse:
    """List books grouped by subfolder for a knowledge source."""
    source = await KnowledgeSource.get(db, source_id, DEMO_USER_ID)
    book_docs = await Document.get_books_by_source(db, source.id)

    # Group book documents by subfolder
    grouped: dict[str, list[Document]] = {}
    for doc in book_docs:
        folder = BookSchema.folder_from_path(doc.relative_path)
        if folder:
            grouped.setdefault(folder, []).append(doc)

    # Build BookSchema for each group
    books: list[BookSchema] = []
    for folder_path, docs in sorted(grouped.items()):
        note_doc = next((d for d in docs if d.content_type == ContentType.BOOK_NOTE), None)
        meta = note_doc.doc_metadata or {} if note_doc else {}

        title = meta.get("title") or (note_doc.title if note_doc else None) or folder_path.split("/")[-1]

        book_documents = [
            BookDocumentSummary(
                id=d.id,
                content_type=ContentType(d.content_type),
                status=DocumentStatus(d.status),
                chunk_count=d.chunk_count,
                error_message=d.error_message,
            )
            for d in docs
        ]

        books.append(
            BookSchema(
                folder_path=folder_path,
                title=title,
                author=meta.get("author"),
                tags=meta.get("tags"),
                documents=book_documents,
            )
        )

    return BookListResponse(books=books)

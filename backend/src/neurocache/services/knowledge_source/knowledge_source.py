import logging
import uuid

from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.schemas.knowledge_source import (
    KnowledgeSourceCreateSchema,
    KnowledgeSourceSchema,
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
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

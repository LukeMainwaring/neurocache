import logging

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
        is_valid, error_message = await validate_obsidian_vault()
        if is_valid:
            source = await KnowledgeSource.update_status(db, source.id, DEMO_USER_ID, KnowledgeSourceStatus.CONNECTED)
        else:
            source = await KnowledgeSource.update_status(
                db, source.id, DEMO_USER_ID, KnowledgeSourceStatus.ERROR, error_message
            )
    return source

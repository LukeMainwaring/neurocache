"""Obsidian vault validation service."""

import logging
from pathlib import Path

from neurocache.core.config import get_settings
from neurocache.services.knowledge_source.ingestion import discover_markdown_files

logger = logging.getLogger(__name__)

VAULT_CONTAINER_PATH = "/vault"

config = get_settings()


async def validate_obsidian_vault(
    user_file_path: str,
) -> tuple[bool, str | None, int]:
    """
    Validate the configured Obsidian vault at /vault.

    The vault is mounted at a fixed container path via docker-compose.
    Compares the user-provided path against the configured OBSIDIAN_VAULT_PATH
    to catch mismatches early.

    Args:
        user_file_path: The file path the user entered in the form.

    Returns:
        (is_valid, error_message, file_count) - error_message is None if valid
    """

    if config.OBSIDIAN_VAULT_PATH and user_file_path != config.OBSIDIAN_VAULT_PATH:
        return (
            False,
            f"Path mismatch: entered '{user_file_path}' but server is configured "
            f"with '{config.OBSIDIAN_VAULT_PATH}'. Update the path or your .env file.",
            0,
        )

    container_path = Path(VAULT_CONTAINER_PATH)

    if not container_path.exists():
        return False, "Vault not mounted. Check OBSIDIAN_VAULT_PATH in .env", 0

    if not container_path.is_dir():
        return False, "Vault mount is not a directory", 0

    obsidian_dir = container_path / ".obsidian"
    if not obsidian_dir.exists() or not obsidian_dir.is_dir():
        return False, "Not a valid Obsidian vault (missing .obsidian directory)", 0

    markdown_files = discover_markdown_files(container_path)
    file_count = len(markdown_files)

    logger.info(
        "Validated Obsidian vault at %s (%d markdown files)",
        VAULT_CONTAINER_PATH,
        file_count,
    )
    return True, None, file_count

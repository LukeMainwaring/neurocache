"""Obsidian vault validation service."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

VAULT_CONTAINER_PATH = "/vault"


async def validate_obsidian_vault() -> tuple[bool, str | None]:
    """
    Validate the configured Obsidian vault at /vault.

    The vault is mounted at a fixed container path via docker-compose.

    Returns:
        (is_valid, error_message) - error_message is None if valid
    """
    container_path = Path(VAULT_CONTAINER_PATH)

    if not container_path.exists():
        return False, "Vault not mounted. Check OBSIDIAN_VAULT_PATH in .env"

    if not container_path.is_dir():
        return False, "Vault mount is not a directory"

    obsidian_dir = container_path / ".obsidian"
    if not obsidian_dir.exists() or not obsidian_dir.is_dir():
        return False, "Not a valid Obsidian vault (missing .obsidian directory)"

    logger.info("Validated Obsidian vault at %s", VAULT_CONTAINER_PATH)
    return True, None

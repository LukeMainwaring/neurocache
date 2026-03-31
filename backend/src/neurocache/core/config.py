"""Application configuration using Pydantic Settings."""

import pathlib
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """API and CORS configuration."""

    API_PREFIX: str = "/api"
    ALLOWED_ORIGINS: dict[str, list[str]] = {
        "development": ["http://localhost:3000"],
        "production": ["https://neurocache.vercel.app"],
    }


class BaseAgentSettings(BaseSettings):
    """Base agent configuration."""

    AGENT_MODEL: str = "gpt-5-mini"


class EmbeddingSettings(BaseSettings):
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 1536


class PostgresSettings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int


class BookAnalysisSettings(BaseSettings):
    """Book analysis agent configuration."""

    BOOK_ANALYSIS_MODEL: str = "gpt-5-mini"


class ExtractionSettings(BaseSettings):
    """Conversation-to-knowledge extraction agent configuration."""

    EXTRACTION_MODEL: str = "gpt-5-mini"


class ObsidianSettings(BaseSettings):
    """Obsidian vault configuration."""

    OBSIDIAN_VAULT_PATH: str | None = None  # Host path, e.g., /Users/luke/Documents/Vault
    OBSIDIAN_VAULT_NAME: str = "My Obsidian Vault"  # Default display name


class MCPSettings(BaseSettings):
    """MCP server configuration."""

    NEUROCACHE_USER_ID: str | None = None  # Auth0 user ID for MCP server access


class Auth0Settings(BaseSettings):
    """Auth0 authentication configuration."""

    AUTH0_DOMAIN: str = ""
    AUTH0_API_AUDIENCE: str = ""
    AUTH0_ALGORITHMS: str = "RS256"

    @property
    def auth0_issuer(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/"

    @property
    def auth0_jwks_url(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"


class Settings(
    ApiSettings,
    EmbeddingSettings,
    BaseAgentSettings,
    BookAnalysisSettings,
    ExtractionSettings,
    PostgresSettings,
    ObsidianSettings,
    Auth0Settings,
    MCPSettings,
):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=str(pathlib.Path(__file__).parent.parent.parent.parent / ".env"),
        env_ignore_empty=True,
    )

    ENVIRONMENT: Literal["development", "production"] = "development"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings.model_validate({})

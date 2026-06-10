"""Configuration: load Neo4j credentials from .env and resolve data directory."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import DirectoryPath, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved once at import time — stable regardless of cwd.
_PKG_DIR = Path(__file__).resolve().parent
_ENV_FILE = _PKG_DIR.parent.parent / ".env"
_LAB_SETUP_DIR = _PKG_DIR.parent.parent.parent
_DATA_DIR = _LAB_SETUP_DIR / "aircraft_digital_twin_data_v2"
_DOCUMENT_DIR = _LAB_SETUP_DIR / "aircraft_digital_twin_data"


class Settings(BaseSettings):
    """Neo4j connection settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
    )

    neo4j_uri: str
    neo4j_username: str = "neo4j"
    neo4j_password: SecretStr

    data_dir: DirectoryPath = _DATA_DIR  # type: ignore[assignment]
    document_dir: DirectoryPath = _DOCUMENT_DIR  # type: ignore[assignment]

    # OpenAI embeddings — required for the `setup` command.
    openai_api_key: SecretStr | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # OpenAI chat model — used by the `setup` command for entity extraction.
    openai_extraction_model: str = "gpt-5-mini"
    openai_extraction_max_completion_tokens: int = 8000

    # LLM provider selection — "openai" or "anthropic".
    llm_provider: Literal["openai", "anthropic"] = "openai"

    # Anthropic — only required when llm_provider is "anthropic".
    anthropic_api_key: SecretStr | None = None
    anthropic_extraction_model: str = "claude-sonnet-4-6"
    anthropic_extraction_max_tokens: int = 8000

    # Chunking settings for the `setup` command.
    chunk_size: int = 800
    chunk_overlap: int = 100

    # Limit chunks processed per document during setup (0 = no limit).
    enrich_sample_size: int = 0

    # Number of rows to show per section in the `samples` command.
    sample_size: int = 10

    @model_validator(mode="after")
    def _check_uri_scheme(self) -> Settings:
        if not self.neo4j_uri.startswith(("neo4j://", "neo4j+s://", "neo4j+ssc://", "bolt://", "bolt+s://", "bolt+ssc://")):
            raise ValueError(
                f"NEO4J_URI must start with a valid scheme (neo4j+s://, bolt+s://, etc.), got: {self.neo4j_uri}"
            )
        return self

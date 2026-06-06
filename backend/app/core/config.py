from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "RepoLens API"
    app_version: str = "0.1.0"
    environment: str = field(default_factory=lambda: os.getenv("REPOLENS_ENV", "development"))
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "REPOLENS_DATABASE_URL",
            "sqlite:///./.repolens/repolens.sqlite",
        )
    )
    qdrant_url: str = field(
        default_factory=lambda: os.getenv("REPOLENS_QDRANT_URL", "http://localhost:6333")
    )
    workspace_root: Path = field(
        default_factory=lambda: Path(os.getenv("REPOLENS_WORKSPACE_ROOT", ".repolens/repos"))
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv(
                "REPOLENS_CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            )
        )
    )
    chat_model: str = field(default_factory=lambda: os.getenv("REPOLENS_CHAT_MODEL", ""))
    chat_base_url: str = field(default_factory=lambda: os.getenv("REPOLENS_CHAT_BASE_URL", ""))
    chat_api_key: str = field(default_factory=lambda: os.getenv("REPOLENS_CHAT_API_KEY", ""))
    chat_temperature: float = field(
        default_factory=lambda: _optional_float(os.getenv("REPOLENS_CHAT_TEMPERATURE", "")) or 0.2
    )
    chat_timeout_seconds: float = field(
        default_factory=lambda: _optional_float(os.getenv("REPOLENS_CHAT_TIMEOUT_SECONDS", "")) or 60.0
    )
    embedding_base_url: str = field(
        default_factory=lambda: os.getenv("REPOLENS_EMBEDDING_BASE_URL", "")
    )
    embedding_api_key: str = field(
        default_factory=lambda: os.getenv("REPOLENS_EMBEDDING_API_KEY", "")
    )
    embedding_model: str = field(
        default_factory=lambda: os.getenv("REPOLENS_EMBEDDING_MODEL", "")
    )
    embedding_dimension: int | None = field(
        default_factory=lambda: _optional_int(os.getenv("REPOLENS_EMBEDDING_DIMENSION", ""))
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def _optional_int(value: str) -> int | None:
    if not value.strip():
        return None
    return int(value)


def _optional_float(value: str) -> float | None:
    if not value.strip():
        return None
    return float(value)

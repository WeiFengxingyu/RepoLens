from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    audit_enabled: bool


def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("APP_ENV", "demo"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///demo.sqlite"),
        audit_enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true",
    )

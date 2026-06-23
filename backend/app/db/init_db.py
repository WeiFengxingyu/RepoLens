from pathlib import Path

from sqlalchemy import text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401

_PHASE7_TOOL_CALL_COLUMNS = {
    "client_name": "VARCHAR(128)",
    "client_session_id": "VARCHAR(128)",
    "permission_policy": "VARCHAR(64)",
    "input_hash": "VARCHAR(64)",
    "output_hash": "VARCHAR(64)",
}

_PHASE7_TOOL_CALL_INDEXES = {
    "ix_tool_calls_client_name": "client_name",
    "ix_tool_calls_client_session_id": "client_session_id",
    "ix_tool_calls_permission_policy": "permission_policy",
}


def init_db() -> None:
    settings = get_settings()
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.removeprefix("sqlite:///")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _ensure_phase7_tool_call_columns()


def _ensure_phase7_tool_call_columns() -> None:
    with engine.begin() as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
        if "tool_calls" not in table_names:
            return

        existing_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(tool_calls)"))
        }
        for column_name, column_type in _PHASE7_TOOL_CALL_COLUMNS.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE tool_calls ADD COLUMN {column_name} {column_type}")
                )

        for index_name, column_name in _PHASE7_TOOL_CALL_INDEXES.items():
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS {index_name} "
                    f"ON tool_calls ({column_name})"
                )
            )

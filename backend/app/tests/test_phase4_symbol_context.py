from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import pytest

from app.db.base import Base
from app.models import CodeChunk, CodeRelation, RelationType, Repository, RepositoryStatus, SymbolType
from app.services.tools import (
    SYMBOL_CONTEXT_MAX_NEIGHBORS,
    SymbolContextError,
    get_symbol_context,
)


def test_get_symbol_context_returns_symbol_and_graph_neighbors() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        fixture = _insert_symbol_context_fixture(db)

        result = get_symbol_context(
            db,
            fixture["repository_id"],
            "helper",
            file_path="app.py",
            max_neighbors=5,
        )

    assert result.symbol.chunk_id == fixture["helper_id"]
    assert result.symbol.file_path == "app.py"
    assert result.symbol.symbol_name == "helper"

    neighbors = {(neighbor.symbol_name, neighbor.relation_type, neighbor.direction) for neighbor in result.neighbors}
    assert ("main", RelationType.CALLS.value, "in") in neighbors
    assert ("format_value", RelationType.CALLS.value, "out") in neighbors
    assert ("types", RelationType.IMPORTS.value, "out") in neighbors
    assert result.to_dict()["symbol"]["symbol_name"] == "helper"


def test_get_symbol_context_deduplicates_same_file_neighbors() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        fixture = _insert_symbol_context_fixture(db)

        result = get_symbol_context(db, fixture["repository_id"], "helper", file_path="app.py")

    main_neighbors = [neighbor for neighbor in result.neighbors if neighbor.symbol_name == "main"]
    assert len(main_neighbors) == 1
    assert main_neighbors[0].relation_type == RelationType.CALLS.value
    assert main_neighbors[0].direction == "in"


def test_get_symbol_context_filters_ambiguous_symbol_by_file_path() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        fixture = _insert_symbol_context_fixture(db)

        ambiguous = get_symbol_context(db, fixture["repository_id"], "helper")
        filtered = get_symbol_context(
            db,
            fixture["repository_id"],
            "helper",
            file_path="other.py",
        )

    assert ambiguous.symbol.file_path == "app.py"
    assert ambiguous.warnings
    assert filtered.symbol.file_path == "other.py"
    assert filtered.warnings == []


def test_get_symbol_context_respects_max_neighbors() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        fixture = _insert_symbol_context_fixture(db)

        result = get_symbol_context(
            db,
            fixture["repository_id"],
            "helper",
            file_path="app.py",
            max_neighbors=2,
        )

    assert len(result.neighbors) == 2


def test_get_symbol_context_validates_input_and_missing_symbol() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        fixture = _insert_symbol_context_fixture(db)

        with pytest.raises(SymbolContextError, match="symbol_name"):
            get_symbol_context(db, fixture["repository_id"], "   ")

        with pytest.raises(SymbolContextError, match=str(SYMBOL_CONTEXT_MAX_NEIGHBORS)):
            get_symbol_context(
                db,
                fixture["repository_id"],
                "helper",
                max_neighbors=SYMBOL_CONTEXT_MAX_NEIGHBORS + 1,
            )

        with pytest.raises(SymbolContextError, match="not found"):
            get_symbol_context(db, fixture["repository_id"], "missing")


def _insert_symbol_context_fixture(db: Session) -> dict[str, str]:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
        chunk_count=5,
        relation_count=3,
    )
    db.add(repository)
    db.flush()

    main = _chunk(repository.id, "app.py", "main", 1, 2)
    helper = _chunk(repository.id, "app.py", "helper", 4, 7)
    formatter = _chunk(repository.id, "formatters.py", "format_value", 1, 3)
    types = _chunk(repository.id, "types.py", "types", 1, 4, symbol_type=SymbolType.FILE.value)
    other_helper = _chunk(repository.id, "other.py", "helper", 1, 2)
    db.add_all([main, helper, formatter, types, other_helper])
    db.flush()

    db.add_all(
        [
            _relation(repository.id, main, helper, RelationType.CALLS.value),
            _relation(repository.id, helper, formatter, RelationType.CALLS.value),
            _relation(repository.id, helper, types, RelationType.IMPORTS.value),
        ]
    )
    db.commit()
    return {
        "repository_id": repository.id,
        "main_id": main.id,
        "helper_id": helper.id,
        "formatter_id": formatter.id,
        "types_id": types.id,
        "other_helper_id": other_helper.id,
    }


def _chunk(
    repository_id: str,
    file_path: str,
    symbol_name: str,
    start_line: int,
    end_line: int,
    *,
    symbol_type: str = SymbolType.FUNCTION.value,
) -> CodeChunk:
    return CodeChunk(
        repository_id=repository_id,
        file_path=file_path,
        language="python",
        symbol_name=symbol_name,
        symbol_type=symbol_type,
        start_line=start_line,
        end_line=end_line,
        content_hash=f"hash-{file_path}-{symbol_name}-{start_line}",
        content=f"def {symbol_name}():\n    pass\n",
    )


def _relation(
    repository_id: str,
    source: CodeChunk,
    target: CodeChunk,
    relation_type: str,
) -> CodeRelation:
    return CodeRelation(
        repository_id=repository_id,
        source_id=source.id,
        target_id=target.id,
        source_symbol=source.symbol_name,
        target_symbol=target.symbol_name,
        relation_type=relation_type,
        source_file=source.file_path,
        target_file=target.file_path,
    )

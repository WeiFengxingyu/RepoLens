import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import pytest

from app.db.base import Base
from app.models import CodeChunk, CodeRelation, RelationType, Repository, RepositoryStatus, SymbolType
from app.services.review import (
    DiffMapperError,
    map_diff_to_symbols,
    write_changed_by_relations,
)
from app.services.tools import analyze_diff


def test_map_diff_to_symbols_matches_changed_lines_to_smallest_chunks() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_diff_mapper_fixture(db)
        mapping = map_diff_to_symbols(db, repository_id, _analysis_for_app_change())

    assert mapping.match_count == 2
    assert mapping.unmatched_count == 0
    matches = {(match.line_type, match.line, match.symbol_name) for match in mapping.matches}
    assert ("added", 6, "helper") in matches
    assert ("removed", 11, "main") in matches
    assert mapping.to_dict()["match_count"] == 2


def test_map_diff_to_symbols_falls_back_to_file_level_chunk() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_diff_mapper_fixture(db)
        analysis = analyze_diff(
            """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -17,1 +17,1 @@
-old_module_value = 1
+new_module_value = 2
"""
        )

        mapping = map_diff_to_symbols(db, repository_id, analysis)

    assert mapping.match_count == 2
    assert {match.symbol_name for match in mapping.matches} == {"app.py"}
    assert {match.symbol_type for match in mapping.matches} == {SymbolType.FILE.value}


def test_map_diff_to_symbols_records_unmatched_lines_without_fake_symbols() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_diff_mapper_fixture(db)
        analysis = analyze_diff(
            """diff --git a/missing.py b/missing.py
--- a/missing.py
+++ b/missing.py
@@ -1,1 +1,1 @@
-old()
+new()
"""
        )

        mapping = map_diff_to_symbols(db, repository_id, analysis)

    assert mapping.match_count == 0
    assert mapping.unmatched_count == 2
    assert {line.reason for line in mapping.unmatched_lines} == {"no_chunk_for_changed_line"}


def test_write_changed_by_relations_replaces_same_task_relations_only() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_diff_mapper_fixture(db)
        old_relation = CodeRelation(
            repository_id=repository_id,
            source_id=None,
            target_id=None,
            source_symbol="old",
            target_symbol="diff",
            relation_type=RelationType.CHANGED_BY.value,
            source_file="app.py",
            target_file="app.py",
            extra_metadata=json.dumps({"task_id": "task-old"}),
        )
        same_task_relation = CodeRelation(
            repository_id=repository_id,
            source_id=None,
            target_id=None,
            source_symbol="stale",
            target_symbol="diff",
            relation_type=RelationType.CHANGED_BY.value,
            source_file="app.py",
            target_file="app.py",
            extra_metadata=json.dumps({"task_id": "task-1"}),
        )
        db.add_all([old_relation, same_task_relation])
        db.commit()

        mapping = map_diff_to_symbols(db, repository_id, _analysis_for_app_change())
        written = write_changed_by_relations(db, repository_id, "task-1", mapping)
        db.commit()

        stored = db.scalars(
            select(CodeRelation)
            .where(
                CodeRelation.repository_id == repository_id,
                CodeRelation.relation_type == RelationType.CHANGED_BY.value,
            )
            .order_by(CodeRelation.source_symbol)
        ).all()

    assert len(written) == 2
    assert len(stored) == 3
    assert {relation.source_symbol for relation in stored} == {"helper", "main", "old"}
    written_metadata = [
        json.loads(relation.extra_metadata or "{}")
        for relation in stored
        if relation.source_symbol in {"helper", "main"}
    ]
    assert {metadata["task_id"] for metadata in written_metadata} == {"task-1"}
    assert {metadata["line_type"] for metadata in written_metadata} == {"added", "removed"}


def test_write_changed_by_relations_validates_task_and_repository() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_diff_mapper_fixture(db)
        mapping = map_diff_to_symbols(db, repository_id, _analysis_for_app_change())

        with pytest.raises(DiffMapperError, match="task_id"):
            write_changed_by_relations(db, repository_id, " ", mapping)

        with pytest.raises(DiffMapperError, match="repository_id"):
            write_changed_by_relations(db, "other-repo", "task-1", mapping)


def _analysis_for_app_change():
    return analyze_diff(
        """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -10,3 +4,4 @@
 context_before
-return old_main()
 context_after
+return helper()
"""
    )


def _insert_diff_mapper_fixture(db: Session) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
        chunk_count=3,
    )
    db.add(repository)
    db.flush()
    db.add_all(
        [
            _chunk(repository.id, "app.py", "app.py", SymbolType.FILE.value, 1, 20),
            _chunk(repository.id, "app.py", "helper", SymbolType.FUNCTION.value, 4, 8),
            _chunk(repository.id, "app.py", "main", SymbolType.FUNCTION.value, 10, 13),
        ]
    )
    db.commit()
    return repository.id


def _chunk(
    repository_id: str,
    file_path: str,
    symbol_name: str,
    symbol_type: str,
    start_line: int,
    end_line: int,
) -> CodeChunk:
    return CodeChunk(
        repository_id=repository_id,
        file_path=file_path,
        language="python",
        symbol_name=symbol_name,
        symbol_type=symbol_type,
        start_line=start_line,
        end_line=end_line,
        content_hash=f"hash-{symbol_name}-{start_line}",
        content=f"{symbol_name}\n",
    )

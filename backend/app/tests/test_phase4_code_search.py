from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import pytest

from app.core.config import get_settings
from app.db.base import Base
from app.models import CodeChunk, CodeRelation, RelationType, Repository, RepositoryStatus, SymbolType
from app.services.tools import CODE_SEARCH_MAX_TOP_K, CodeSearchError, code_search


def test_code_search_returns_evidence_compatible_results_and_debug(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_code_search_fixture(db)

        result = code_search(
            db,
            repository_id,
            "main helper",
            get_settings(),
            top_k=5,
            use_bm25=True,
            use_vector=True,
            use_graph=True,
        )

    assert result.repository_id == repository_id
    assert result.query == "main helper"
    assert result.evidences
    assert result.debug.bm25_count >= 1
    assert result.debug.vector_count == 0
    assert result.debug.graph_count >= 1
    assert result.debug.evidence_count == len(result.evidences)
    assert result.debug.vector_disabled_reason is not None
    assert result.warnings

    first = result.evidences[0]
    assert first.repository_id == repository_id
    assert first.file_path == "app.py"
    assert first.start_line >= 1
    assert first.snippet
    assert "evidences" in result.to_dict()
    assert result.to_dict()["debug"]["evidence_count"] == len(result.evidences)


def test_code_search_skips_vector_warning_when_vector_disabled_by_option(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_code_search_fixture(db)

        result = code_search(
            db,
            repository_id,
            "main helper",
            get_settings(),
            top_k=5,
            use_bm25=True,
            use_vector=False,
            use_graph=True,
        )

    assert result.debug.vector_disabled_reason is None
    assert result.warnings == []
    assert result.debug.vector_count == 0
    assert result.evidences


def test_code_search_returns_empty_result_for_repository_without_chunks(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository = Repository(
            name="empty",
            source_type="local",
            local_path="empty",
            status=RepositoryStatus.READY.value,
        )
        db.add(repository)
        db.commit()

        result = code_search(db, repository.id, "anything", get_settings(), use_vector=False)

    assert result.evidences == []
    assert result.debug.evidence_count == 0
    assert result.debug.bm25_count == 0


def test_code_search_validates_query_top_k_and_sources(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        with pytest.raises(CodeSearchError, match="query"):
            code_search(db, "repo", "   ", get_settings())

        with pytest.raises(CodeSearchError, match=str(CODE_SEARCH_MAX_TOP_K)):
            code_search(db, "repo", "query", get_settings(), top_k=CODE_SEARCH_MAX_TOP_K + 1)

        with pytest.raises(CodeSearchError, match="retrieval source"):
            code_search(
                db,
                "repo",
                "query",
                get_settings(),
                use_bm25=False,
                use_vector=False,
                use_graph=False,
            )


def _insert_code_search_fixture(db: Session) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
        chunk_count=2,
        relation_count=1,
    )
    db.add(repository)
    db.flush()

    main_chunk = CodeChunk(
        repository_id=repository.id,
        file_path="app.py",
        language="python",
        symbol_name="main",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=1,
        end_line=2,
        content_hash="hash-main",
        content="def main():\n    return helper()\n",
    )
    helper_chunk = CodeChunk(
        repository_id=repository.id,
        file_path="app.py",
        language="python",
        symbol_name="helper",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=4,
        end_line=5,
        content_hash="hash-helper",
        content="def helper():\n    return 2\n",
    )
    db.add_all([main_chunk, helper_chunk])
    db.flush()
    db.add(
        CodeRelation(
            repository_id=repository.id,
            source_id=main_chunk.id,
            target_id=helper_chunk.id,
            source_symbol="main",
            target_symbol="helper",
            relation_type=RelationType.CALLS.value,
            source_file="app.py",
            target_file="app.py",
        )
    )
    db.commit()
    return repository.id


def _clear_embedding_env(monkeypatch) -> None:
    monkeypatch.delenv("REPOLENS_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_DIMENSION", raising=False)
    get_settings.cache_clear()

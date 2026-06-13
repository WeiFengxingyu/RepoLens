from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.models import CodeChunk, Repository, RepositoryStatus, SymbolType
from app.services.evaluation import (
    BM25_VECTOR_STRATEGY,
    EvaluationSample,
    EvaluationSampleType,
    run_bm25_vector_sample,
)


def test_run_bm25_vector_sample_keeps_bm25_when_vector_disabled(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_repository_with_chunk(db)
        result = run_bm25_vector_sample(
            db,
            _location_sample(),
            repository_id=repository_id,
            settings=get_settings(),
            top_k=5,
        )

    assert result.sample_id == "loc-001"
    assert result.strategy == BM25_VECTOR_STRATEGY
    assert result.bm25_count >= 1
    assert result.vector_count == 0
    assert result.evidence_count >= 1
    assert result.evidences[0].file_path == "app/services/repositories.py"
    assert "bm25" in result.evidences[0].sources
    assert result.vector_unavailable is True
    assert result.vector_disabled_reason is not None
    assert "REPOLENS_EMBEDDING_BASE_URL" in result.vector_disabled_reason
    assert result.error_message is None
    assert result.to_dict()["strategy"] == "bm25_vector"
    assert result.to_dict()["bm25_count"] >= 1


def test_run_bm25_vector_sample_calls_retrieval_with_bm25_vector_options(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_retrieve_repository(
        db,
        repository_id,
        query,
        settings,
        *,
        top_k,
        use_bm25,
        use_vector,
        use_graph,
    ):
        captured.update(
            {
                "repository_id": repository_id,
                "query": query,
                "top_k": top_k,
                "use_bm25": use_bm25,
                "use_vector": use_vector,
                "use_graph": use_graph,
            }
        )
        return _fake_retrieval_result(repository_id)

    monkeypatch.setattr(
        "app.services.evaluation.runner.retrieve_repository",
        fake_retrieve_repository,
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        result = run_bm25_vector_sample(
            db,
            _location_sample(),
            repository_id="repo-1",
            settings=get_settings(),
            top_k=3,
        )

    assert captured == {
        "repository_id": "repo-1",
        "query": "Where is RepositoryImportService repository import implemented?",
        "top_k": 3,
        "use_bm25": True,
        "use_vector": True,
        "use_graph": False,
    }
    assert result.bm25_count == 1
    assert result.vector_count == 1
    assert result.evidence_count == 1
    assert result.evidences[0].sources == ["bm25", "vector"]
    assert result.vector_unavailable is False


def test_run_bm25_vector_sample_uses_review_context_query(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_retrieve_repository(
        db,
        repository_id,
        query,
        settings,
        *,
        top_k,
        use_bm25,
        use_vector,
        use_graph,
    ):
        captured["query"] = query
        return _fake_retrieval_result(repository_id)

    monkeypatch.setattr(
        "app.services.evaluation.runner.retrieve_repository",
        fake_retrieve_repository,
    )
    review_sample = EvaluationSample(
        id="review-001",
        type=EvaluationSampleType.REVIEW,
        repository_key="python_demo",
        question="Review this token expiration change.",
        expected_files=["app/auth/tokens.py"],
        expected_symbols=["validate_access_token"],
        review_diff="diff --git a/app/auth/tokens.py b/app/auth/tokens.py",
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        result = run_bm25_vector_sample(
            db,
            review_sample,
            repository_id="repo-1",
            settings=get_settings(),
        )

    assert "Review this token expiration change." in str(captured["query"])
    assert "app/auth/tokens.py" in str(captured["query"])
    assert "validate_access_token" in str(captured["query"])
    assert result.sample_type == "review"


def test_run_bm25_vector_sample_returns_failed_result_on_retrieval_error(monkeypatch) -> None:
    def fake_retrieve_repository(*args, **kwargs):
        raise RuntimeError("retrieval exploded")

    monkeypatch.setattr(
        "app.services.evaluation.runner.retrieve_repository",
        fake_retrieve_repository,
    )
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        result = run_bm25_vector_sample(
            db,
            _location_sample(),
            repository_id="repo-1",
            settings=get_settings(),
        )

    assert result.failed is True
    assert result.error_message == "retrieval exploded"
    assert result.evidence_count == 0
    assert result.bm25_count == 0
    assert result.vector_count == 0


def _location_sample() -> EvaluationSample:
    return EvaluationSample(
        id="loc-001",
        type=EvaluationSampleType.LOCATION,
        repository_key="python_demo",
        question="Where is RepositoryImportService repository import implemented?",
        expected_files=["app/services/repositories.py"],
        expected_symbols=["RepositoryImportService"],
    )


def _insert_repository_with_chunk(db: Session) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
        chunk_count=1,
    )
    db.add(repository)
    db.flush()
    db.add(
        CodeChunk(
            repository_id=repository.id,
            file_path="app/services/repositories.py",
            language="python",
            symbol_name="RepositoryImportService",
            symbol_type=SymbolType.CLASS.value,
            start_line=1,
            end_line=20,
            content_hash="hash-import-service",
            content="class RepositoryImportService:\n    pass\n",
        )
    )
    db.commit()
    return repository.id


def _fake_retrieval_result(repository_id: str):
    from app.services.retrieval import RetrievalDebug, RetrievalResult
    from app.services.retrieval.context import ContextPackage
    from app.services.retrieval.evidence import Evidence

    evidence = Evidence(
        evidence_id="ev-1",
        chunk_id="chunk-1",
        repository_id=repository_id,
        file_path="app/services/repositories.py",
        start_line=1,
        end_line=20,
        symbol_name="RepositoryImportService",
        symbol_type="class",
        language="python",
        source="vector",
        sources=["bm25", "vector"],
        score=0.91,
        bm25_score=0.7,
        vector_score=0.91,
        graph_score=0.0,
        snippet="class RepositoryImportService:\n    pass\n",
        metadata={},
    )
    return RetrievalResult(
        repository_id=repository_id,
        query="query",
        evidences=[evidence],
        context=ContextPackage(
            evidences=[evidence],
            context_text="",
            total_chars=0,
            truncated=False,
        ),
        debug=RetrievalDebug(
            bm25_count=1,
            vector_count=1,
            graph_count=0,
            merged_count=1,
            evidence_count=1,
            vector_disabled_reason=None,
            context_truncated=False,
        ),
    )


def _clear_embedding_env(monkeypatch) -> None:
    monkeypatch.delenv("REPOLENS_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_DIMENSION", raising=False)
    get_settings.cache_clear()

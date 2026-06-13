import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import CodeChunk, Repository, RepositoryStatus, SymbolType
from app.services.evaluation import EvaluationEvidenceRef
from app.services.evaluation.runner import (
    BM25_VECTOR_GRAPH_STRATEGY,
    BM25_VECTOR_STRATEGY,
    VECTOR_ONLY_STRATEGY,
    BM25VectorEvaluationResult,
    BM25VectorGraphEvaluationResult,
    VectorOnlyEvaluationResult,
)


def test_evaluation_api_runs_all_strategies_and_persists_results(tmp_path, monkeypatch) -> None:
    dataset_path = _write_dataset(tmp_path)
    _patch_runners(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/evaluations",
        json={
            "name": "P5 API smoke",
            "dataset_path": str(dataset_path),
            "strategy": "all",
            "repository_map": {"python_demo": repository_id},
            "top_k": 5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["sample_count"] == 2
    assert [metric["strategy"] for metric in body["metrics"]] == [
        "vector_only",
        "bm25_vector",
        "bm25_vector_graph",
    ]
    assert len(body["results"]) == 6
    assert body["warnings"] == []
    assert body["metrics"][0]["hit_at_5"] == 1.0
    assert body["metrics"][0]["error_count"] == 0
    assert body["results"][0]["matched_files"]
    assert body["results"][0]["citations"]

    list_response = client.get("/api/evaluations")
    assert list_response.status_code == 200
    assert list_response.json()[0]["run_id"] == body["run_id"]

    get_response = client.get(f"/api/evaluations/{body['run_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["run_id"] == body["run_id"]
    assert len(get_response.json()["results"]) == 6


def test_evaluation_api_runs_single_strategy(tmp_path, monkeypatch) -> None:
    dataset_path = _write_dataset(tmp_path)
    _patch_runners(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/evaluations",
        json={
            "name": "single",
            "dataset_path": str(dataset_path),
            "strategy": "bm25_vector_graph",
            "repository_map": {"python_demo": repository_id},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert [metric["strategy"] for metric in body["metrics"]] == ["bm25_vector_graph"]
    assert {result["strategy"] for result in body["results"]} == {"bm25_vector_graph"}


def test_evaluation_api_resolves_dataset_path_from_repository_root(monkeypatch) -> None:
    _patch_runners(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        python_repository_id = _insert_repository(db, name="python_demo")
        ts_repository_id = _insert_repository(db, name="ts_demo")

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/evaluations",
        json={
            "name": "repository relative",
            "dataset_path": "evals/datasets/p0_plus_eval.jsonl",
            "strategy": "bm25_vector_graph",
            "repository_map": {
                "python_demo": python_repository_id,
                "ts_demo": ts_repository_id,
            },
            "top_k": 5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["sample_count"] == 50
    assert body["metrics"][0]["sample_count"] == 50


def test_evaluation_api_rejects_missing_repository_map_key(tmp_path) -> None:
    dataset_path = _write_dataset(tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/evaluations",
        json={
            "dataset_path": str(dataset_path),
            "strategy": "vector_only",
            "repository_map": {},
        },
    )

    assert response.status_code == 422
    assert "repository_map missing keys" in response.json()["detail"]


def test_evaluation_api_rejects_repository_before_ready(tmp_path) -> None:
    dataset_path = _write_dataset(tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        repository = Repository(
            name="demo",
            source_type="local",
            local_path="demo",
            status=RepositoryStatus.PARSING.value,
        )
        db.add(repository)
        db.commit()
        repository_id = repository.id

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/evaluations",
        json={
            "dataset_path": str(dataset_path),
            "strategy": "vector_only",
            "repository_map": {"python_demo": repository_id},
        },
    )

    assert response.status_code == 400
    assert "must be ready" in response.json()["detail"]


def test_get_evaluation_returns_404_for_missing_run() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.get("/api/evaluations/missing")

    assert response.status_code == 404


def _write_dataset(tmp_path: Path) -> Path:
    dataset_path = tmp_path / "eval.jsonl"
    samples = [
        {
            "id": "loc-001",
            "type": "location",
            "repository_key": "python_demo",
            "question": "Where is main?",
            "expected_files": ["app.py"],
            "expected_symbols": ["main"],
        },
        {
            "id": "exp-001",
            "type": "explanation",
            "repository_key": "python_demo",
            "question": "Explain helper.",
            "expected_files": ["helper.py"],
            "expected_symbols": ["helper"],
        },
    ]
    dataset_path.write_text(
        "\n".join(json.dumps(sample) for sample in samples),
        encoding="utf-8",
    )
    return dataset_path


def _insert_repository(db: Session, name: str = "demo") -> str:
    repository = Repository(
        name=name,
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
        chunk_count=2,
    )
    db.add(repository)
    db.flush()
    db.add_all(
        [
            CodeChunk(
                repository_id=repository.id,
                file_path="app.py",
                language="python",
                symbol_name="main",
                symbol_type=SymbolType.FUNCTION.value,
                start_line=1,
                end_line=2,
                content_hash="hash-main",
                content="def main():\n    return helper()\n",
            ),
            CodeChunk(
                repository_id=repository.id,
                file_path="helper.py",
                language="python",
                symbol_name="helper",
                symbol_type=SymbolType.FUNCTION.value,
                start_line=1,
                end_line=2,
                content_hash="hash-helper",
                content="def helper():\n    return 1\n",
            ),
        ]
    )
    db.commit()
    return repository.id


def _patch_runners(monkeypatch) -> None:
    def fake_vector(db, sample, *, repository_id, settings, top_k):
        return VectorOnlyEvaluationResult(
            sample_id=sample.id,
            sample_type=sample.type.value,
            repository_key=sample.repository_key,
            repository_id=repository_id,
            strategy=VECTOR_ONLY_STRATEGY,
            query=sample.question,
            evidence_count=1,
            vector_count=1,
            latency_ms=10,
            evidences=[_evidence_for_sample(sample)],
        )

    def fake_bm25_vector(db, sample, *, repository_id, settings, top_k):
        return BM25VectorEvaluationResult(
            sample_id=sample.id,
            sample_type=sample.type.value,
            repository_key=sample.repository_key,
            repository_id=repository_id,
            strategy=BM25_VECTOR_STRATEGY,
            query=sample.question,
            evidence_count=1,
            bm25_count=1,
            vector_count=1,
            latency_ms=20,
            evidences=[_evidence_for_sample(sample)],
        )

    def fake_bm25_vector_graph(db, sample, *, repository_id, settings, top_k):
        return BM25VectorGraphEvaluationResult(
            sample_id=sample.id,
            sample_type=sample.type.value,
            repository_key=sample.repository_key,
            repository_id=repository_id,
            strategy=BM25_VECTOR_GRAPH_STRATEGY,
            query=sample.question,
            evidence_count=1,
            bm25_count=1,
            vector_count=1,
            graph_count=1,
            latency_ms=30,
            evidences=[_evidence_for_sample(sample)],
        )

    monkeypatch.setattr("app.services.evaluation.service.run_vector_only_sample", fake_vector)
    monkeypatch.setattr("app.services.evaluation.service.run_bm25_vector_sample", fake_bm25_vector)
    monkeypatch.setattr(
        "app.services.evaluation.service.run_bm25_vector_graph_sample",
        fake_bm25_vector_graph,
    )


def _evidence_for_sample(sample) -> EvaluationEvidenceRef:
    return EvaluationEvidenceRef(
        evidence_id=f"ev-{sample.id}",
        chunk_id=f"chunk-{sample.id}",
        file_path=sample.expected_files[0],
        start_line=1,
        end_line=2,
        symbol_name=sample.expected_symbols[0],
        score=0.8,
        sources=["bm25"],
    )


def _override_get_db(TestingSessionLocal):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override_get_db

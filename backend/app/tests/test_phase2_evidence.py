import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import CodeChunk, Repository, RepositoryStatus, SymbolType
from app.services.retrieval import (
    RankedRetrievalCandidate,
    build_evidences,
    build_snippet,
    evidence_id_for,
)


def test_build_evidences_combines_ranked_candidates_with_chunk_metadata() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id, chunk_id = _insert_evidence_fixture(db)
        evidences = build_evidences(
            db,
            repository_id,
            [
                RankedRetrievalCandidate(
                    chunk_id=chunk_id,
                    sources=["bm25", "vector", "graph_expand"],
                    final_score=0.78,
                    bm25_score=0.5,
                    vector_score=1.0,
                    graph_score=0.6,
                    metadata={"raw_scores": {"vector": 0.9}},
                )
            ],
        )

    assert len(evidences) == 1
    evidence = evidences[0]
    assert evidence.evidence_id == evidence_id_for(
        repository_id,
        chunk_id,
        ["bm25", "vector", "graph_expand"],
        1,
    )
    assert evidence.chunk_id == chunk_id
    assert evidence.repository_id == repository_id
    assert evidence.file_path == "app.py"
    assert evidence.start_line == 1
    assert evidence.end_line == 2
    assert evidence.symbol_name == "main"
    assert evidence.symbol_type == SymbolType.FUNCTION.value
    assert evidence.language == "python"
    assert evidence.source == "vector"
    assert evidence.sources == ["bm25", "vector", "graph_expand"]
    assert evidence.score == 0.78
    assert evidence.bm25_score == 0.5
    assert evidence.vector_score == 1.0
    assert evidence.graph_score == 0.6
    assert evidence.snippet == "def main():\n    return 1"
    assert evidence.metadata["raw_scores"] == {"vector": 0.9}


def test_build_evidences_skips_missing_or_cross_repository_chunks() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id, chunk_id = _insert_evidence_fixture(db)
        other_repository = Repository(
            name="other",
            source_type="local",
            local_path="other",
            status=RepositoryStatus.READY.value,
        )
        db.add(other_repository)
        db.commit()
        other_repository_id = other_repository.id
        evidences = build_evidences(
            db,
            other_repository_id,
            [
                RankedRetrievalCandidate(
                    chunk_id=chunk_id,
                    sources=["bm25"],
                    final_score=0.3,
                    bm25_score=1.0,
                ),
                RankedRetrievalCandidate(
                    chunk_id="missing",
                    sources=["vector"],
                    final_score=0.2,
                    vector_score=1.0,
                ),
            ],
        )

    assert repository_id != other_repository_id
    assert evidences == []


def test_build_evidences_chooses_primary_source_from_available_sources() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id, chunk_id = _insert_evidence_fixture(db)
        evidence = build_evidences(
            db,
            repository_id,
            [
                RankedRetrievalCandidate(
                    chunk_id=chunk_id,
                    sources=["bm25"],
                    final_score=0.3,
                    bm25_score=0.0,
                )
            ],
        )[0]

    assert evidence.source == "bm25"


def test_evidence_id_and_snippet_truncation_are_stable() -> None:
    evidence_id = evidence_id_for("repo-1", "chunk-1", ["bm25", "vector"], 2)

    assert evidence_id == hashlib.sha256(
        "repo-1:chunk-1:bm25,vector:2".encode("utf-8")
    ).hexdigest()

    content = "\n".join([f"line {index}" for index in range(1, 8)])
    assert build_snippet(content, max_lines=3, max_chars=4000) == "line 1\nline 2\nline 3\n..."
    assert build_snippet("abcdef", max_lines=40, max_chars=3) == "abc\n..."


def _insert_evidence_fixture(db: Session) -> tuple[str, str]:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
    )
    db.add(repository)
    db.flush()
    chunk = CodeChunk(
        repository_id=repository.id,
        file_path="app.py",
        language="python",
        symbol_name="main",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=1,
        end_line=2,
        content_hash="hash-main",
        content="def main():\n    return 1",
    )
    db.add(chunk)
    db.commit()
    return repository.id, chunk.id

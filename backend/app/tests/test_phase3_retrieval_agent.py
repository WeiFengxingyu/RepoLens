from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.models import CodeChunk, CodeRelation, RelationType, Repository, RepositoryStatus, SymbolType
from app.services.agent import RetrievalOptions, plan_question, retrieve_for_plan


def test_retrieval_agent_runs_plan_queries_and_deduplicates_evidence(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_fixture(db)
        plan = plan_question("How does main call helper?")

        result = retrieve_for_plan(
            db,
            repository_id,
            plan,
            get_settings(),
            options=RetrievalOptions(top_k=5, use_vector=False),
        )

    assert result.evidences
    assert len({evidence.chunk_id for evidence in result.evidences}) == len(result.evidences)
    assert result.context_text
    assert len(result.tool_calls) == len(plan.retrieval_queries)
    assert all(tool_call.tool_name == "code_search" for tool_call in result.tool_calls)
    assert all(tool_call.success for tool_call in result.tool_calls)
    assert result.debug_counts["query_count"] == len(plan.retrieval_queries)
    assert result.debug_counts["final_evidence_count"] == len(result.evidences)


def test_retrieval_agent_preserves_vector_disabled_warning(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository_id = _insert_fixture(db)
        plan = plan_question("Where is helper implemented?")

        result = retrieve_for_plan(
            db,
            repository_id,
            plan,
            get_settings(),
            options=RetrievalOptions(top_k=3, use_vector=True),
        )

    assert result.evidences
    assert result.warnings
    assert "Vector retrieval disabled" in result.warnings[0]


def _insert_fixture(db: Session) -> str:
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

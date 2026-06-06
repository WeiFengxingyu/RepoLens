from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    CodeChunk,
    CodeLanguage,
    CodeRelation,
    RelationType,
    Repository,
    RepositorySourceType,
    RepositoryStatus,
    SymbolType,
)


def test_phase1_tables_are_created() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    tables = set(inspect(engine).get_table_names())

    assert {"repositories", "code_chunks", "code_relations"}.issubset(tables)


def test_repository_chunk_relation_round_trip() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        repository = Repository(
            name="demo",
            source_type=RepositorySourceType.LOCAL.value,
            local_path="F:/Desktop/demo",
            language_summary='{"python": 1}',
            status=RepositoryStatus.READY.value,
            file_count=1,
            parsed_file_count=1,
            skipped_file_count=0,
            chunk_count=1,
            relation_count=1,
        )
        session.add(repository)
        session.flush()

        chunk = CodeChunk(
            repository_id=repository.id,
            file_path="app.py",
            language=CodeLanguage.PYTHON.value,
            symbol_name="main",
            symbol_type=SymbolType.FUNCTION.value,
            start_line=1,
            end_line=3,
            content_hash="0" * 64,
            content="def main():\n    return 1\n",
        )
        session.add(chunk)
        session.flush()

        relation = CodeRelation(
            repository_id=repository.id,
            source_id=chunk.id,
            source_symbol="main",
            relation_type=RelationType.DEFINED_IN.value,
            source_file="app.py",
            target_file="app.py",
        )
        session.add(relation)
        session.commit()

        stored = session.get(Repository, repository.id)

        assert stored is not None
        assert stored.chunks[0].symbol_name == "main"
        assert stored.relations[0].relation_type == RelationType.DEFINED_IN.value


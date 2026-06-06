from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import CodeChunk, CodeRelation, RelationType, Repository, RepositoryStatus, SymbolType
from app.services.graph import (
    code_graph_stats,
    expand_graph_neighbors,
    get_callees,
    get_callers,
    get_import_neighbors,
    get_neighbors,
    get_same_file_chunks,
    load_code_graph,
)


def test_load_code_graph_builds_nodes_and_edges_from_chunks_and_relations() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_graph_fixture(db)
        relation_count = db.scalar(
            select(func.count()).select_from(CodeRelation).where(
                CodeRelation.repository_id == repository_id
            )
        )

        graph = load_code_graph(db, repository_id)

    assert graph.graph["repository_id"] == repository_id
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1

    main_node = next(
        node_id for node_id, attrs in graph.nodes(data=True) if attrs["symbol_name"] == "main"
    )
    helper_node = next(
        node_id for node_id, attrs in graph.nodes(data=True) if attrs["symbol_name"] == "helper"
    )
    assert graph.nodes[main_node]["file_path"] == "app.py"
    assert graph.nodes[main_node]["symbol_type"] == SymbolType.FUNCTION.value
    assert graph.has_edge(main_node, helper_node)
    assert graph.edges[main_node, helper_node]["relation_type"] == RelationType.CALLS.value

    stats = code_graph_stats(graph, repository_id, relation_count or 0)
    assert stats.node_count == 2
    assert stats.edge_count == 1
    assert stats.skipped_relation_count == 1


def test_load_code_graph_returns_empty_graph_for_missing_repository() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        graph = load_code_graph(db, "missing-repository")

    assert graph.graph["repository_id"] == "missing-repository"
    assert graph.number_of_nodes() == 0
    assert graph.number_of_edges() == 0


def test_code_graph_neighbor_queries_return_expected_graph_candidates() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_neighbor_fixture(db)
        graph = load_code_graph(db, repository_id)

    chunk_ids = _chunk_ids_by_symbol(graph)
    main_id = chunk_ids["main"]
    helper_id = chunk_ids["helper"]
    caller_id = chunk_ids["cli"]
    dependency_id = chunk_ids["dependency"]

    callers = get_callers(graph, main_id)
    assert [candidate.chunk_id for candidate in callers] == [caller_id]
    assert callers[0].source == "graph_expand"
    assert callers[0].relation_type == RelationType.CALLS.value
    assert callers[0].graph_score == 0.6

    callees = get_callees(graph, main_id)
    assert [candidate.chunk_id for candidate in callees] == [helper_id]

    same_file_chunks = get_same_file_chunks(graph, main_id)
    assert [candidate.chunk_id for candidate in same_file_chunks] == [helper_id]
    assert same_file_chunks[0].relation_type == "same_file"
    assert same_file_chunks[0].graph_score == 0.8

    import_neighbors = get_import_neighbors(graph, main_id)
    assert [candidate.chunk_id for candidate in import_neighbors] == [dependency_id]
    assert import_neighbors[0].relation_type == RelationType.IMPORTS.value
    assert import_neighbors[0].graph_score == 0.5

    neighbors = get_neighbors(graph, main_id, depth=1)
    assert {candidate.chunk_id for candidate in neighbors} == {
        caller_id,
        helper_id,
        dependency_id,
    }
    assert {candidate.seed_chunk_id for candidate in neighbors} == {main_id}
    assert {candidate.graph_distance for candidate in neighbors} == {1}


def test_expand_graph_neighbors_deduplicates_and_limits_results() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_neighbor_fixture(db)
        graph = load_code_graph(db, repository_id)

    chunk_ids = _chunk_ids_by_symbol(graph)
    expanded = expand_graph_neighbors(graph, [chunk_ids["main"]], top_k=2)

    assert [candidate.chunk_id for candidate in expanded] == [
        chunk_ids["helper"],
        chunk_ids["cli"],
    ]
    assert expanded[0].relation_type == "same_file"
    assert expanded[0].graph_score == 0.8
    assert expanded[1].relation_type == RelationType.CALLS.value
    assert expanded[1].graph_score == 0.6


def test_code_graph_neighbor_queries_return_empty_for_missing_or_invalid_inputs() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        graph = load_code_graph(db, "missing-repository")

    assert get_neighbors(graph, "missing") == []
    assert get_neighbors(graph, "missing", depth=0) == []
    assert get_callers(graph, "missing") == []
    assert get_callees(graph, "missing") == []
    assert get_same_file_chunks(graph, "missing") == []
    assert get_import_neighbors(graph, "missing") == []
    assert expand_graph_neighbors(graph, ["missing"], top_k=0) == []


def _insert_graph_fixture(db: Session) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
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
    db.add_all(
        [
            CodeRelation(
                repository_id=repository.id,
                source_id=main_chunk.id,
                target_id=helper_chunk.id,
                source_symbol="main",
                target_symbol="helper",
                relation_type=RelationType.CALLS.value,
                source_file="app.py",
                target_file="app.py",
            ),
            CodeRelation(
                repository_id=repository.id,
                source_id=main_chunk.id,
                target_id=None,
                source_symbol="main",
                target_symbol="json",
                relation_type=RelationType.IMPORTS.value,
                source_file="app.py",
                target_file=None,
            ),
        ]
    )
    db.commit()
    return repository.id


def _insert_neighbor_fixture(db: Session) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
    )
    db.add(repository)
    db.flush()
    caller_chunk = _chunk(repository.id, "cli.py", "cli", 1, "def cli():\n    return main()\n")
    main_chunk = _chunk(repository.id, "app.py", "main", 1, "def main():\n    return helper()\n")
    helper_chunk = _chunk(repository.id, "app.py", "helper", 4, "def helper():\n    return 2\n")
    dependency_chunk = _chunk(
        repository.id,
        "dependency.py",
        "dependency",
        1,
        "def dependency():\n    return 3\n",
    )
    db.add_all([caller_chunk, main_chunk, helper_chunk, dependency_chunk])
    db.flush()
    db.add_all(
        [
            _relation(repository.id, caller_chunk.id, main_chunk.id, "cli", "main", RelationType.CALLS),
            _relation(
                repository.id,
                main_chunk.id,
                helper_chunk.id,
                "main",
                "helper",
                RelationType.CALLS,
            ),
            _relation(
                repository.id,
                main_chunk.id,
                dependency_chunk.id,
                "main",
                "dependency",
                RelationType.IMPORTS,
            ),
        ]
    )
    db.commit()
    return repository.id


def _chunk(
    repository_id: str,
    file_path: str,
    symbol_name: str,
    start_line: int,
    content: str,
) -> CodeChunk:
    return CodeChunk(
        repository_id=repository_id,
        file_path=file_path,
        language="python",
        symbol_name=symbol_name,
        symbol_type=SymbolType.FUNCTION.value,
        start_line=start_line,
        end_line=start_line + 1,
        content_hash=f"hash-{symbol_name}",
        content=content,
    )


def _relation(
    repository_id: str,
    source_id: str,
    target_id: str,
    source_symbol: str,
    target_symbol: str,
    relation_type: RelationType,
) -> CodeRelation:
    return CodeRelation(
        repository_id=repository_id,
        source_id=source_id,
        target_id=target_id,
        source_symbol=source_symbol,
        target_symbol=target_symbol,
        relation_type=relation_type.value,
        source_file="app.py",
        target_file="app.py",
    )


def _chunk_ids_by_symbol(graph) -> dict[str, str]:
    return {attrs["symbol_name"]: node_id for node_id, attrs in graph.nodes(data=True)}

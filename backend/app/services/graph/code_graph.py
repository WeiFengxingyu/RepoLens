from dataclasses import dataclass

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CodeChunk, CodeRelation, RelationType

GRAPH_RELATION_WEIGHTS = {
    "same_file": 0.8,
    RelationType.CONTAINS.value: 0.7,
    RelationType.DEFINED_IN.value: 0.6,
    RelationType.CALLS.value: 0.6,
    RelationType.IMPORTS.value: 0.5,
}


@dataclass(frozen=True)
class CodeGraphStats:
    repository_id: str
    node_count: int
    edge_count: int
    skipped_relation_count: int


@dataclass(frozen=True)
class GraphExpansionCandidate:
    chunk_id: str
    score: float
    graph_score: float
    graph_distance: int
    seed_chunk_id: str
    relation_type: str
    metadata: dict[str, object]
    source: str = "graph_expand"


def load_code_graph(db: Session, repository_id: str) -> nx.DiGraph:
    graph = nx.DiGraph(repository_id=repository_id)
    chunks = db.scalars(
        select(CodeChunk)
        .where(CodeChunk.repository_id == repository_id)
        .order_by(CodeChunk.file_path, CodeChunk.start_line, CodeChunk.id)
    ).all()

    for chunk in chunks:
        graph.add_node(
            chunk.id,
            repository_id=chunk.repository_id,
            file_path=chunk.file_path,
            symbol_name=chunk.symbol_name,
            symbol_type=chunk.symbol_type,
            language=chunk.language,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            content_hash=chunk.content_hash,
        )

    chunk_ids = set(graph.nodes)
    relations = db.scalars(
        select(CodeRelation)
        .where(CodeRelation.repository_id == repository_id)
        .order_by(CodeRelation.source_file, CodeRelation.source_symbol, CodeRelation.id)
    ).all()
    for relation in relations:
        if relation.source_id not in chunk_ids or relation.target_id not in chunk_ids:
            continue
        graph.add_edge(
            relation.source_id,
            relation.target_id,
            relation_id=relation.id,
            relation_type=relation.relation_type,
            source_symbol=relation.source_symbol,
            target_symbol=relation.target_symbol,
            source_file=relation.source_file,
            target_file=relation.target_file,
            metadata=relation.extra_metadata,
        )

    return graph


def code_graph_stats(graph: nx.DiGraph, repository_id: str, relation_count: int) -> CodeGraphStats:
    return CodeGraphStats(
        repository_id=repository_id,
        node_count=graph.number_of_nodes(),
        edge_count=graph.number_of_edges(),
        skipped_relation_count=max(relation_count - graph.number_of_edges(), 0),
    )


def get_neighbors(graph: nx.DiGraph, chunk_id: str, depth: int = 1) -> list[GraphExpansionCandidate]:
    if depth <= 0 or chunk_id not in graph:
        return []

    visited = {chunk_id}
    frontier = [chunk_id]
    candidates: list[GraphExpansionCandidate] = []
    for distance in range(1, depth + 1):
        next_frontier: list[str] = []
        for current_id in frontier:
            for neighbor_id in _ordered_adjacent_nodes(graph, current_id):
                if neighbor_id in visited:
                    continue
                relation_type = _relation_type_between(graph, current_id, neighbor_id)
                candidates.append(
                    _graph_candidate(
                        graph,
                        chunk_id=neighbor_id,
                        seed_chunk_id=chunk_id,
                        relation_type=relation_type,
                        distance=distance,
                    )
                )
                visited.add(neighbor_id)
                next_frontier.append(neighbor_id)
        frontier = next_frontier
    return _sort_candidates(candidates)


def get_callers(graph: nx.DiGraph, chunk_id: str) -> list[GraphExpansionCandidate]:
    if chunk_id not in graph:
        return []
    return _sort_candidates(
        [
            _graph_candidate(
                graph,
                chunk_id=predecessor_id,
                seed_chunk_id=chunk_id,
                relation_type=RelationType.CALLS.value,
                distance=1,
            )
            for predecessor_id in graph.predecessors(chunk_id)
            if graph.edges[predecessor_id, chunk_id].get("relation_type")
            == RelationType.CALLS.value
        ]
    )


def get_callees(graph: nx.DiGraph, chunk_id: str) -> list[GraphExpansionCandidate]:
    if chunk_id not in graph:
        return []
    return _sort_candidates(
        [
            _graph_candidate(
                graph,
                chunk_id=successor_id,
                seed_chunk_id=chunk_id,
                relation_type=RelationType.CALLS.value,
                distance=1,
            )
            for successor_id in graph.successors(chunk_id)
            if graph.edges[chunk_id, successor_id].get("relation_type") == RelationType.CALLS.value
        ]
    )


def get_same_file_chunks(graph: nx.DiGraph, chunk_id: str) -> list[GraphExpansionCandidate]:
    if chunk_id not in graph:
        return []
    file_path = graph.nodes[chunk_id].get("file_path")
    return _sort_candidates(
        [
            _graph_candidate(
                graph,
                chunk_id=node_id,
                seed_chunk_id=chunk_id,
                relation_type="same_file",
                distance=1,
            )
            for node_id, attrs in graph.nodes(data=True)
            if node_id != chunk_id and attrs.get("file_path") == file_path
        ]
    )


def get_import_neighbors(graph: nx.DiGraph, chunk_id: str) -> list[GraphExpansionCandidate]:
    if chunk_id not in graph:
        return []
    candidates = []
    for successor_id in graph.successors(chunk_id):
        if graph.edges[chunk_id, successor_id].get("relation_type") == RelationType.IMPORTS.value:
            candidates.append(
                _graph_candidate(
                    graph,
                    chunk_id=successor_id,
                    seed_chunk_id=chunk_id,
                    relation_type=RelationType.IMPORTS.value,
                    distance=1,
                )
            )
    for predecessor_id in graph.predecessors(chunk_id):
        if graph.edges[predecessor_id, chunk_id].get("relation_type") == RelationType.IMPORTS.value:
            candidates.append(
                _graph_candidate(
                    graph,
                    chunk_id=predecessor_id,
                    seed_chunk_id=chunk_id,
                    relation_type=RelationType.IMPORTS.value,
                    distance=1,
                )
            )
    return _sort_candidates(candidates)


def expand_graph_neighbors(
    graph: nx.DiGraph,
    seed_chunk_ids: list[str],
    *,
    depth: int = 1,
    top_k: int = 10,
) -> list[GraphExpansionCandidate]:
    if top_k <= 0:
        return []

    best_by_chunk_id: dict[str, GraphExpansionCandidate] = {}
    for seed_chunk_id in seed_chunk_ids:
        for candidate in [
            *get_neighbors(graph, seed_chunk_id, depth=depth),
            *get_same_file_chunks(graph, seed_chunk_id),
        ]:
            if candidate.chunk_id == seed_chunk_id:
                continue
            current = best_by_chunk_id.get(candidate.chunk_id)
            if current is None or candidate.graph_score > current.graph_score:
                best_by_chunk_id[candidate.chunk_id] = candidate

    return _sort_candidates(list(best_by_chunk_id.values()))[:top_k]


def _ordered_adjacent_nodes(graph: nx.DiGraph, chunk_id: str) -> list[str]:
    adjacent = set(graph.successors(chunk_id)) | set(graph.predecessors(chunk_id))
    return sorted(adjacent, key=lambda node_id: _node_sort_key(graph, node_id))


def _relation_type_between(graph: nx.DiGraph, source_id: str, target_id: str) -> str:
    if graph.has_edge(source_id, target_id):
        return str(graph.edges[source_id, target_id].get("relation_type", "related"))
    if graph.has_edge(target_id, source_id):
        return str(graph.edges[target_id, source_id].get("relation_type", "related"))
    return "related"


def _graph_candidate(
    graph: nx.DiGraph,
    *,
    chunk_id: str,
    seed_chunk_id: str,
    relation_type: str,
    distance: int,
) -> GraphExpansionCandidate:
    weight = GRAPH_RELATION_WEIGHTS.get(relation_type, 0.4)
    graph_score = weight / max(distance, 1)
    return GraphExpansionCandidate(
        chunk_id=chunk_id,
        score=graph_score,
        graph_score=graph_score,
        graph_distance=distance,
        seed_chunk_id=seed_chunk_id,
        relation_type=relation_type,
        metadata=dict(graph.nodes[chunk_id]),
    )


def _sort_candidates(candidates: list[GraphExpansionCandidate]) -> list[GraphExpansionCandidate]:
    return sorted(
        candidates,
        key=lambda candidate: (
            -candidate.graph_score,
            candidate.graph_distance,
            _node_sort_key_from_metadata(candidate.metadata),
        ),
    )


def _node_sort_key(graph: nx.DiGraph, node_id: str) -> tuple[str, int, str]:
    return _node_sort_key_from_metadata(dict(graph.nodes[node_id]))


def _node_sort_key_from_metadata(metadata: dict[str, object]) -> tuple[str, int, str]:
    file_path = metadata.get("file_path")
    start_line = metadata.get("start_line")
    symbol_name = metadata.get("symbol_name")
    return (
        str(file_path) if file_path is not None else "",
        int(start_line) if isinstance(start_line, int) else 0,
        str(symbol_name) if symbol_name is not None else "",
    )

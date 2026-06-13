from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CodeChunk
from app.services.graph import load_code_graph

SYMBOL_CONTEXT_MAX_NEIGHBORS = 50
DEFAULT_SYMBOL_CONTEXT_NEIGHBORS = 8


class SymbolContextError(ValueError):
    """Raised when symbol context cannot be built within the tool contract."""


@dataclass(frozen=True)
class SymbolContextSymbol:
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str
    language: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "language": self.language,
        }


@dataclass(frozen=True)
class SymbolContextNeighbor:
    chunk_id: str
    relation_type: str
    direction: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str
    language: str
    graph_distance: int = 1

    def to_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "relation_type": self.relation_type,
            "direction": self.direction,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "language": self.language,
            "graph_distance": self.graph_distance,
        }


@dataclass(frozen=True)
class SymbolContextResult:
    symbol: SymbolContextSymbol
    neighbors: list[SymbolContextNeighbor]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol.to_dict(),
            "neighbors": [neighbor.to_dict() for neighbor in self.neighbors],
            "warnings": self.warnings,
        }


def get_symbol_context(
    db: Session,
    repository_id: str,
    symbol_name: str,
    *,
    file_path: str | None = None,
    max_neighbors: int = DEFAULT_SYMBOL_CONTEXT_NEIGHBORS,
) -> SymbolContextResult:
    normalized_symbol = " ".join(symbol_name.strip().split())
    if not normalized_symbol:
        raise SymbolContextError("symbol_name is required.")
    if max_neighbors < 1 or max_neighbors > SYMBOL_CONTEXT_MAX_NEIGHBORS:
        raise SymbolContextError(
            f"max_neighbors must be between 1 and {SYMBOL_CONTEXT_MAX_NEIGHBORS}."
        )

    normalized_file_path = _normalize_file_path(file_path)
    matches = _find_symbol_chunks(
        db,
        repository_id,
        normalized_symbol,
        file_path=normalized_file_path,
    )
    if not matches:
        raise SymbolContextError("Symbol was not found in this repository.")

    selected = matches[0]
    warnings = []
    if len(matches) > 1 and normalized_file_path is None:
        warnings.append(
            "Multiple symbol matches were found; selected the first by file path and line number."
        )

    graph = load_code_graph(db, repository_id)
    neighbors = _collect_neighbors(graph, selected.id, max_neighbors=max_neighbors)
    return SymbolContextResult(
        symbol=_symbol_from_chunk(selected),
        neighbors=neighbors,
        warnings=warnings,
    )


def _find_symbol_chunks(
    db: Session,
    repository_id: str,
    symbol_name: str,
    *,
    file_path: str | None,
) -> list[CodeChunk]:
    statement = (
        select(CodeChunk)
        .where(
            CodeChunk.repository_id == repository_id,
            CodeChunk.symbol_name == symbol_name,
        )
        .order_by(CodeChunk.file_path, CodeChunk.start_line, CodeChunk.id)
    )
    if file_path is not None:
        statement = statement.where(CodeChunk.file_path == file_path)
    return list(db.scalars(statement).all())


def _collect_neighbors(graph, chunk_id: str, *, max_neighbors: int) -> list[SymbolContextNeighbor]:
    if chunk_id not in graph:
        return []

    neighbors_by_id: dict[str, SymbolContextNeighbor] = {}
    for predecessor_id in sorted(graph.predecessors(chunk_id), key=lambda node_id: _node_sort_key(graph, node_id)):
        edge = graph.edges[predecessor_id, chunk_id]
        _add_neighbor(
            neighbors_by_id,
            _neighbor_from_graph(
                graph,
                predecessor_id,
                relation_type=str(edge.get("relation_type", "related")),
                direction="in",
            ),
        )

    for successor_id in sorted(graph.successors(chunk_id), key=lambda node_id: _node_sort_key(graph, node_id)):
        edge = graph.edges[chunk_id, successor_id]
        _add_neighbor(
            neighbors_by_id,
            _neighbor_from_graph(
                graph,
                successor_id,
                relation_type=str(edge.get("relation_type", "related")),
                direction="out",
            ),
        )

    file_path = graph.nodes[chunk_id].get("file_path")
    same_file_ids = [
        node_id
        for node_id, attrs in graph.nodes(data=True)
        if node_id != chunk_id and attrs.get("file_path") == file_path
    ]
    for node_id in sorted(same_file_ids, key=lambda item: _node_sort_key(graph, item)):
        _add_neighbor(
            neighbors_by_id,
            _neighbor_from_graph(
                graph,
                node_id,
                relation_type="same_file",
                direction="same_file",
            ),
        )

    return list(neighbors_by_id.values())[:max_neighbors]


def _add_neighbor(
    neighbors_by_id: dict[str, SymbolContextNeighbor],
    neighbor: SymbolContextNeighbor,
) -> None:
    if neighbor.chunk_id not in neighbors_by_id:
        neighbors_by_id[neighbor.chunk_id] = neighbor


def _neighbor_from_graph(
    graph,
    node_id: str,
    *,
    relation_type: str,
    direction: str,
) -> SymbolContextNeighbor:
    attrs = graph.nodes[node_id]
    return SymbolContextNeighbor(
        chunk_id=node_id,
        relation_type=relation_type,
        direction=direction,
        file_path=str(attrs.get("file_path") or ""),
        start_line=int(attrs.get("start_line") or 0),
        end_line=int(attrs.get("end_line") or 0),
        symbol_name=str(attrs.get("symbol_name") or ""),
        symbol_type=str(attrs.get("symbol_type") or ""),
        language=str(attrs.get("language") or ""),
    )


def _symbol_from_chunk(chunk: CodeChunk) -> SymbolContextSymbol:
    return SymbolContextSymbol(
        chunk_id=chunk.id,
        file_path=chunk.file_path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        symbol_name=chunk.symbol_name,
        symbol_type=chunk.symbol_type,
        language=chunk.language,
    )


def _node_sort_key(graph, node_id: str) -> tuple[str, int, str]:
    attrs = graph.nodes[node_id]
    return (
        str(attrs.get("file_path") or ""),
        int(attrs.get("start_line") or 0),
        str(attrs.get("symbol_name") or ""),
    )


def _normalize_file_path(file_path: str | None) -> str | None:
    if file_path is None:
        return None
    normalized = file_path.strip().replace("\\", "/")
    return normalized or None

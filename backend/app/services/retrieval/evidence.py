from dataclasses import dataclass, field
import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CodeChunk
from app.services.retrieval.rerank import RankedRetrievalCandidate

DEFAULT_SNIPPET_MAX_LINES = 40
DEFAULT_SNIPPET_MAX_CHARS = 4000
PRIMARY_SOURCE_ORDER = ["vector", "bm25", "graph_expand"]


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    chunk_id: str
    repository_id: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str
    language: str
    source: str
    sources: list[str]
    score: float
    bm25_score: float
    vector_score: float
    graph_score: float
    snippet: str
    metadata: dict[str, object] = field(default_factory=dict)


def build_evidences(
    db: Session,
    repository_id: str,
    ranked_candidates: list[RankedRetrievalCandidate],
    *,
    max_lines: int = DEFAULT_SNIPPET_MAX_LINES,
    max_chars: int = DEFAULT_SNIPPET_MAX_CHARS,
) -> list[Evidence]:
    if not ranked_candidates:
        return []

    chunks_by_id = _load_chunks_by_id(
        db,
        repository_id,
        [candidate.chunk_id for candidate in ranked_candidates],
    )
    evidences: list[Evidence] = []
    for rank, candidate in enumerate(ranked_candidates, start=1):
        chunk = chunks_by_id.get(candidate.chunk_id)
        if chunk is None:
            continue
        evidences.append(
            Evidence(
                evidence_id=evidence_id_for(
                    repository_id,
                    candidate.chunk_id,
                    candidate.sources,
                    rank,
                ),
                chunk_id=chunk.id,
                repository_id=repository_id,
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                symbol_name=chunk.symbol_name,
                symbol_type=chunk.symbol_type,
                language=chunk.language,
                source=_primary_source(candidate),
                sources=candidate.sources,
                score=candidate.final_score,
                bm25_score=candidate.bm25_score,
                vector_score=candidate.vector_score,
                graph_score=candidate.graph_score,
                snippet=build_snippet(chunk.content, max_lines=max_lines, max_chars=max_chars),
                metadata=dict(candidate.metadata),
            )
        )
    return evidences


def evidence_id_for(repository_id: str, chunk_id: str, sources: list[str], rank: int) -> str:
    source_key = ",".join(sources)
    return hashlib.sha256(f"{repository_id}:{chunk_id}:{source_key}:{rank}".encode("utf-8")).hexdigest()


def build_snippet(
    content: str,
    *,
    max_lines: int = DEFAULT_SNIPPET_MAX_LINES,
    max_chars: int = DEFAULT_SNIPPET_MAX_CHARS,
) -> str:
    lines = content.splitlines()
    truncated = False
    if max_lines > 0 and len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    snippet = "\n".join(lines)
    if max_chars > 0 and len(snippet) > max_chars:
        snippet = snippet[:max_chars]
        truncated = True
    if truncated:
        return snippet.rstrip() + "\n..."
    return snippet


def _load_chunks_by_id(
    db: Session,
    repository_id: str,
    chunk_ids: list[str],
) -> dict[str, CodeChunk]:
    if not chunk_ids:
        return {}
    chunks = db.scalars(
        select(CodeChunk).where(
            CodeChunk.repository_id == repository_id,
            CodeChunk.id.in_(chunk_ids),
        )
    ).all()
    return {chunk.id: chunk for chunk in chunks}


def _primary_source(candidate: RankedRetrievalCandidate) -> str:
    scores = {
        "vector": candidate.vector_score,
        "bm25": candidate.bm25_score,
        "graph_expand": candidate.graph_score,
    }
    available_sources = [source for source in PRIMARY_SOURCE_ORDER if source in candidate.sources]
    if not available_sources:
        return "vector"
    return max(available_sources, key=lambda source: scores[source])

from app.services.graph import GraphExpansionCandidate
from app.services.indexing import BM25SearchResult, VectorSearchResult
from app.services.retrieval import merge_candidates


def test_merge_candidates_combines_sources_scores_and_metadata_by_chunk_id() -> None:
    merged = merge_candidates(
        bm25_candidates=[
            BM25SearchResult(chunk_id="chunk-1", score=2.0, matched_terms=["main"]),
        ],
        vector_candidates=[
            VectorSearchResult(
                chunk_id="chunk-1",
                score=0.8,
                vector_score=0.8,
                metadata={"file_path": "app.py", "symbol_name": "main"},
            )
        ],
        graph_candidates=[
            GraphExpansionCandidate(
                chunk_id="chunk-1",
                score=0.6,
                graph_score=0.6,
                graph_distance=1,
                seed_chunk_id="seed-1",
                relation_type="calls",
                metadata={"language": "python"},
            ),
            GraphExpansionCandidate(
                chunk_id="chunk-2",
                score=0.5,
                graph_score=0.5,
                graph_distance=1,
                seed_chunk_id="seed-1",
                relation_type="imports",
                metadata={"file_path": "dependency.py"},
            ),
        ],
    )

    assert [candidate.chunk_id for candidate in merged] == ["chunk-1", "chunk-2"]
    assert merged[0].sources == ["bm25", "vector", "graph_expand"]
    assert merged[0].bm25_score == 2.0
    assert merged[0].vector_score == 0.8
    assert merged[0].graph_score == 0.6
    assert merged[0].metadata["bm25_matched_terms"] == ["main"]
    assert merged[0].metadata["file_path"] == "app.py"
    assert merged[0].metadata["language"] == "python"
    assert merged[0].metadata["seed_chunk_id"] == "seed-1"
    assert merged[0].metadata["relation_type"] == "calls"
    assert merged[1].sources == ["graph_expand"]


def test_merge_candidates_keeps_highest_score_per_source_and_unions_terms() -> None:
    merged = merge_candidates(
        bm25_candidates=[
            BM25SearchResult(chunk_id="chunk-1", score=0.5, matched_terms=["import"]),
            BM25SearchResult(chunk_id="chunk-1", score=1.5, matched_terms=["repository"]),
        ],
        vector_candidates=[
            VectorSearchResult(
                chunk_id="chunk-1",
                score=0.9,
                vector_score=0.9,
                metadata={"file_path": "new.py"},
            ),
            VectorSearchResult(
                chunk_id="chunk-1",
                score=0.2,
                vector_score=0.2,
                metadata={"file_path": "old.py"},
            ),
        ],
    )

    assert len(merged) == 1
    assert merged[0].sources == ["bm25", "vector"]
    assert merged[0].bm25_score == 1.5
    assert merged[0].vector_score == 0.9
    assert merged[0].graph_score == 0.0
    assert merged[0].metadata["bm25_matched_terms"] == ["import", "repository"]
    assert merged[0].metadata["file_path"] == "new.py"


def test_merge_candidates_handles_empty_inputs() -> None:
    assert merge_candidates() == []

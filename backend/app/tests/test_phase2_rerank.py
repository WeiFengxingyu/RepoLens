import pytest

from app.services.retrieval import RetrievalCandidate, rerank_candidates


def test_rerank_candidates_normalizes_scores_and_applies_weighted_formula() -> None:
    candidates = [
        RetrievalCandidate(
            chunk_id="chunk-1",
            sources=["bm25", "vector"],
            bm25_score=2.0,
            vector_score=0.5,
            metadata={"file_path": "src/repository.py", "symbol_name": "RepositoryService"},
        ),
        RetrievalCandidate(
            chunk_id="chunk-2",
            sources=["bm25", "vector", "graph_expand"],
            bm25_score=1.0,
            vector_score=1.0,
            graph_score=0.6,
            metadata={"file_path": "api/routes.py", "symbol_name": "import_repository"},
        ),
    ]

    ranked = rerank_candidates(candidates, "repository service")

    assert [candidate.chunk_id for candidate in ranked] == ["chunk-2", "chunk-1"]
    assert ranked[0].vector_score == 1.0
    assert ranked[0].bm25_score == 0.5
    assert ranked[0].graph_score == 1.0
    assert ranked[0].file_relevance_score == 0.8
    assert ranked[0].final_score == pytest.approx(0.78)
    assert ranked[0].metadata["raw_scores"] == {
        "bm25": 1.0,
        "vector": 1.0,
        "graph": 0.6,
        "file": 0.0,
        "diff": 0.0,
    }

    assert ranked[1].vector_score == 0.5
    assert ranked[1].bm25_score == 1.0
    assert ranked[1].graph_score == 0.0
    assert ranked[1].file_relevance_score == 1.0
    assert ranked[1].final_score == pytest.approx(0.575)


def test_rerank_candidates_respects_top_k_and_stable_tie_order() -> None:
    ranked = rerank_candidates(
        [
            RetrievalCandidate(chunk_id="chunk-b", sources=["bm25"], bm25_score=1.0),
            RetrievalCandidate(chunk_id="chunk-a", sources=["bm25"], bm25_score=1.0),
        ],
        "missing",
        top_k=1,
    )

    assert [candidate.chunk_id for candidate in ranked] == ["chunk-a"]


def test_rerank_candidates_handles_empty_and_zero_score_inputs() -> None:
    assert rerank_candidates([], "repository") == []
    assert rerank_candidates(
        [RetrievalCandidate(chunk_id="chunk-1", sources=[])],
        "",
    )[0].final_score == 0.0
    assert rerank_candidates(
        [RetrievalCandidate(chunk_id="chunk-1", sources=[])],
        "repository",
        top_k=0,
    ) == []

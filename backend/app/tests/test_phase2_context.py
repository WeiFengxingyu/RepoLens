from app.services.retrieval import Evidence, build_context_package


def test_build_context_package_formats_and_limits_evidence_count() -> None:
    evidences = [
        _evidence("ev-1", "chunk-1", "app.py", "main", "def main():\n    return 1", 0.9),
        _evidence("ev-2", "chunk-2", "utils.py", "helper", "def helper():\n    return 2", 0.7),
    ]

    package = build_context_package(evidences, max_evidence_count=1, max_chars=12000)

    assert len(package.evidences) == 1
    assert package.evidences[0].evidence_id == "ev-1"
    assert package.truncated is True
    assert package.total_chars == len(package.context_text)
    assert "[1] app.py:1-2 main (vector, score=0.9000)" in package.context_text
    assert "def main()" in package.context_text
    assert "helper" not in package.context_text


def test_build_context_package_truncates_to_char_budget() -> None:
    package = build_context_package(
        [_evidence("ev-1", "chunk-1", "app.py", "main", "x" * 200, 0.9)],
        max_evidence_count=10,
        max_chars=80,
    )

    assert len(package.evidences) == 1
    assert package.truncated is True
    assert package.total_chars <= 80
    assert package.context_text.endswith("\n...")


def test_build_context_package_handles_empty_or_invalid_limits() -> None:
    evidence = _evidence("ev-1", "chunk-1", "app.py", "main", "def main(): pass", 0.9)

    assert build_context_package([], max_evidence_count=10, max_chars=12000).context_text == ""
    assert build_context_package([evidence], max_evidence_count=0, max_chars=12000).truncated is True
    assert build_context_package([evidence], max_evidence_count=10, max_chars=0).truncated is True


def _evidence(
    evidence_id: str,
    chunk_id: str,
    file_path: str,
    symbol_name: str,
    snippet: str,
    score: float,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        chunk_id=chunk_id,
        repository_id="repo-1",
        file_path=file_path,
        start_line=1,
        end_line=2,
        symbol_name=symbol_name,
        symbol_type="function",
        language="python",
        source="vector",
        sources=["vector"],
        score=score,
        bm25_score=0.0,
        vector_score=1.0,
        graph_score=0.0,
        snippet=snippet,
        metadata={},
    )

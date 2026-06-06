from dataclasses import dataclass

from app.services.indexing import build_bm25_index, document_from_chunk, tokenize


@dataclass(frozen=True)
class FakeChunk:
    id: str
    file_path: str
    language: str
    symbol_name: str
    symbol_type: str
    content: str


def test_tokenize_splits_paths_snake_case_and_camel_case() -> None:
    tokens = tokenize("app/services/repository.py import_repository RepositoryService")

    assert "app" in tokens
    assert "services" in tokens
    assert "repository" in tokens
    assert "import" in tokens
    assert "service" in tokens


def test_document_from_chunk_includes_metadata_and_content_tokens() -> None:
    chunk = FakeChunk(
        id="chunk-1",
        file_path="app/services/repository.py",
        language="python",
        symbol_name="RepositoryService.import_repository",
        symbol_type="method",
        content="def import_repository():\n    return scan_repository()\n",
    )

    document = document_from_chunk(chunk)

    assert document.chunk_id == "chunk-1"
    assert {"repository", "service", "import", "scan"}.issubset(set(document.tokens))


def test_bm25_search_ranks_symbol_and_content_matches() -> None:
    chunks = [
        FakeChunk(
            id="chunk-repo",
            file_path="app/services/repository.py",
            language="python",
            symbol_name="RepositoryService.import_repository",
            symbol_type="method",
            content="scan repository and save code chunks",
        ),
        FakeChunk(
            id="chunk-parser",
            file_path="app/services/parser.py",
            language="python",
            symbol_name="parse_python_source",
            symbol_type="function",
            content="parse ast class and function symbols",
        ),
        FakeChunk(
            id="chunk-ui",
            file_path="frontend/app/page.tsx",
            language="typescript",
            symbol_name="RepositoryPanel",
            symbol_type="function",
            content="render repository status metrics",
        ),
    ]

    index = build_bm25_index(chunks)
    results = index.search("import repository chunks", top_k=2)

    assert [result.chunk_id for result in results] == ["chunk-repo", "chunk-ui"]
    assert results[0].score > results[1].score
    assert {"import", "repository", "chunks"}.issubset(set(results[0].matched_terms))


def test_bm25_search_handles_empty_query_and_top_k() -> None:
    index = build_bm25_index(
        [
            FakeChunk(
                id="chunk-1",
                file_path="app.py",
                language="python",
                symbol_name="main",
                symbol_type="function",
                content="def main(): pass",
            )
        ]
    )

    assert index.search("") == []
    assert index.search("main", top_k=0) == []

from app.chunking.builder import build_chunks
from app.scanner.scanner import scan_repository


class RepositoryImportService:
    """Import repositories by scanning files and building code chunks."""

    def import_repository(self, source: str) -> dict[str, object]:
        if not source.strip():
            raise ValueError("source is required")
        files = scan_repository(source)
        chunks = build_chunks(files)
        return {
            "source": source,
            "file_count": len(files),
            "chunk_count": len(chunks),
            "status": "indexed",
        }

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    CodeChunk,
    CodeLanguage,
    CodeRelation,
    RelationType,
    Repository,
    RepositoryStatus,
    SymbolType,
)
from app.schemas import (
    RepositoryDetail,
    RepositoryImportRequest,
    RepositoryStatusResponse,
    RepositorySummary,
)
from app.services.chunking import ChunkBuilderError, CodeChunkDraft, build_chunks
from app.services.parser import ParsedFile, ParsedRelation, ParserError, parse_source_file
from app.services.repository.providers import ProviderError, choose_provider
from app.services.scanner import ScannerError, scan_repository

SUPPORTED_PARSE_LANGUAGES = {
    CodeLanguage.PYTHON.value,
    CodeLanguage.TYPESCRIPT.value,
    CodeLanguage.JAVASCRIPT.value,
}


class RepositoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def import_repository(self, request: RepositoryImportRequest) -> RepositoryDetail:
        provider = choose_provider(request.source)
        metadata = provider.get_metadata(request.source)
        repository = Repository(
            name=request.name or metadata.name,
            source_type=metadata.source_type,
            source_url=request.source if metadata.source_type != "local" else None,
            local_path="",
            branch=request.branch,
            status=RepositoryStatus.PENDING.value,
        )
        self.db.add(repository)
        self.db.flush()

        try:
            target_dir = self._target_dir(repository.id)
            if metadata.source_type != "local":
                repository.status = RepositoryStatus.CLONING.value
                self.db.flush()
            prepared = provider.prepare(request.source, target_dir, request.branch)
            repository.source_type = prepared.source_type
            repository.source_url = prepared.source_url
            repository.local_path = str(prepared.local_path)
            repository.branch = prepared.branch
            repository.commit_hash = prepared.commit_hash
            repository.status = RepositoryStatus.SCANNING.value
            self.db.flush()

            scan_result = scan_repository(prepared.local_path)
            repository.language_summary = json.dumps(scan_result.language_summary, sort_keys=True)
            repository.file_count = scan_result.file_count
            repository.skipped_file_count = scan_result.skipped_file_count
            repository.status = RepositoryStatus.PARSING.value
            self.db.flush()

            parsed_files = [
                parse_source_file(scanned_file.path, scanned_file.relative_path, scanned_file.language)
                for scanned_file in scan_result.files
                if scanned_file.language in SUPPORTED_PARSE_LANGUAGES
            ]
            repository.parsed_file_count = sum(1 for parsed_file in parsed_files if not parsed_file.errors)
            repository.status = RepositoryStatus.CHUNKING.value
            self.db.flush()

            chunk_count, relation_count = self._save_index_artifacts(repository.id, parsed_files)
            repository.chunk_count = chunk_count
            repository.relation_count = relation_count
            repository.indexed_at = datetime.utcnow()
            repository.error_message = None
            repository.status = RepositoryStatus.READY.value
            self.db.commit()
        except (ProviderError, ScannerError, ParserError, ChunkBuilderError) as exc:
            repository.status = RepositoryStatus.FAILED.value
            repository.error_message = str(exc)
            self.db.commit()

        self.db.refresh(repository)
        return repository_to_detail(repository)

    def list_repositories(self) -> list[RepositorySummary]:
        repositories = self.db.scalars(select(Repository).order_by(Repository.created_at.desc())).all()
        return [repository_to_summary(repository) for repository in repositories]

    def get_repository(self, repository_id: str) -> RepositoryDetail | None:
        repository = self.db.get(Repository, repository_id)
        if repository is None:
            return None
        return repository_to_detail(repository)

    def get_status(self, repository_id: str) -> RepositoryStatusResponse | None:
        repository = self.db.get(Repository, repository_id)
        if repository is None:
            return None
        return RepositoryStatusResponse(
            id=repository.id,
            status=repository.status,
            progress={
                "current_step": repository.status,
                "file_count": repository.file_count,
                "parsed_file_count": repository.parsed_file_count,
                "chunk_count": repository.chunk_count,
                "relation_count": repository.relation_count,
            },
            error_message=repository.error_message,
        )

    def _target_dir(self, repository_id: str) -> Path:
        workspace_root = self.settings.workspace_root
        if not workspace_root.is_absolute():
            workspace_root = Path.cwd() / workspace_root
        target_dir = (workspace_root / repository_id).resolve()
        workspace_root = workspace_root.resolve()
        if workspace_root not in target_dir.parents and target_dir != workspace_root:
            raise ProviderError("Repository target directory escapes workspace root.")
        return target_dir

    def _save_index_artifacts(
        self,
        repository_id: str,
        parsed_files: list[ParsedFile],
    ) -> tuple[int, int]:
        chunk_drafts: list[CodeChunkDraft] = []
        parsed_relations: list[ParsedRelation] = []
        for parsed_file in parsed_files:
            chunk_drafts.extend(build_chunks(parsed_file))
            parsed_relations.extend(parsed_file.relations)

        chunk_records: list[tuple[CodeChunkDraft, CodeChunk]] = []
        for draft in chunk_drafts:
            chunk = CodeChunk(
                repository_id=repository_id,
                file_path=draft.file_path,
                language=draft.language,
                symbol_name=draft.symbol_name,
                symbol_type=draft.symbol_type,
                start_line=draft.start_line,
                end_line=draft.end_line,
                content_hash=draft.content_hash,
                content=draft.content,
                extra_metadata=_dump_metadata(draft.metadata),
            )
            self.db.add(chunk)
            chunk_records.append((draft, chunk))

        self.db.flush()
        chunk_ids = {
            (draft.file_path, draft.symbol_name): chunk.id for draft, chunk in chunk_records
        }
        relation_count = 0

        for relation in parsed_relations:
            self.db.add(
                CodeRelation(
                    repository_id=repository_id,
                    source_id=_lookup_chunk_id(chunk_ids, relation.source_file, relation.source_symbol),
                    target_id=_lookup_chunk_id(
                        chunk_ids,
                        relation.target_file or relation.source_file,
                        relation.target_symbol,
                    ),
                    source_symbol=relation.source_symbol,
                    target_symbol=relation.target_symbol,
                    relation_type=relation.relation_type,
                    source_file=relation.source_file,
                    target_file=relation.target_file,
                    extra_metadata=_dump_metadata(relation.metadata),
                )
            )
            relation_count += 1

        for draft, chunk in chunk_records:
            if draft.symbol_type == SymbolType.FILE.value:
                continue
            self.db.add(
                CodeRelation(
                    repository_id=repository_id,
                    source_id=chunk.id,
                    target_id=_lookup_chunk_id(chunk_ids, draft.file_path, draft.file_path),
                    source_symbol=draft.symbol_name,
                    target_symbol=draft.file_path,
                    relation_type=RelationType.DEFINED_IN.value,
                    source_file=draft.file_path,
                    target_file=draft.file_path,
                    extra_metadata=_dump_metadata({"symbol_type": draft.symbol_type}),
                )
            )
            relation_count += 1

        self.db.flush()
        return len(chunk_records), relation_count


def repository_to_summary(repository: Repository) -> RepositorySummary:
    return RepositorySummary(
        id=repository.id,
        name=repository.name,
        source_type=repository.source_type,
        status=repository.status,
        file_count=repository.file_count,
        chunk_count=repository.chunk_count,
        relation_count=repository.relation_count,
        updated_at=repository.updated_at,
    )


def repository_to_detail(repository: Repository) -> RepositoryDetail:
    return RepositoryDetail(
        id=repository.id,
        name=repository.name,
        source_type=repository.source_type,
        source_url=repository.source_url,
        local_path=repository.local_path,
        branch=repository.branch,
        commit_hash=repository.commit_hash,
        status=repository.status,
        language_summary=_parse_language_summary(repository.language_summary),
        file_count=repository.file_count,
        parsed_file_count=repository.parsed_file_count,
        skipped_file_count=repository.skipped_file_count,
        chunk_count=repository.chunk_count,
        relation_count=repository.relation_count,
        error_message=repository.error_message,
        created_at=repository.created_at,
        updated_at=repository.updated_at,
        indexed_at=repository.indexed_at,
    )


def _parse_language_summary(value: str) -> dict[str, int]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): int(count) for key, count in parsed.items() if isinstance(count, int)}


def _dump_metadata(metadata: dict[str, Any]) -> str | None:
    if not metadata:
        return None
    return json.dumps(metadata, sort_keys=True)


def _lookup_chunk_id(
    chunk_ids: dict[tuple[str, str], str],
    file_path: str | None,
    symbol_name: str | None,
) -> str | None:
    if file_path is None or symbol_name is None:
        return None
    return chunk_ids.get((file_path, symbol_name))

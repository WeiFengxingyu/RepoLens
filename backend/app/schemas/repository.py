from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryImportRequest(BaseModel):
    source: str = Field(min_length=1)
    branch: str | None = None
    name: str | None = None


class RepositorySummary(BaseModel):
    id: str
    name: str
    source_type: str
    status: str
    file_count: int
    chunk_count: int
    relation_count: int
    updated_at: datetime


class RepositoryDetail(BaseModel):
    id: str
    name: str
    source_type: str
    source_url: str | None
    local_path: str
    branch: str | None
    commit_hash: str | None
    status: str
    language_summary: dict[str, int]
    file_count: int
    parsed_file_count: int
    skipped_file_count: int
    chunk_count: int
    relation_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None


class RepositoryStatusResponse(BaseModel):
    id: str
    status: str
    progress: dict[str, int | str]
    error_message: str | None


class VectorIndexResponse(BaseModel):
    repository_id: str
    status: str
    collection_name: str
    chunk_count: int
    vector_count: int
    dimension: int | None


class RetrievalDebugRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)
    use_bm25: bool = True
    use_vector: bool = True
    use_graph: bool = True


class EvidenceResponse(BaseModel):
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
    metadata: dict[str, object]


class RetrievalDebugInfo(BaseModel):
    bm25_count: int
    vector_count: int
    graph_count: int
    merged_count: int
    evidence_count: int
    vector_disabled_reason: str | None
    context_truncated: bool


class RetrievalDebugResponse(BaseModel):
    repository_id: str
    query: str
    evidences: list[EvidenceResponse]
    debug: RetrievalDebugInfo

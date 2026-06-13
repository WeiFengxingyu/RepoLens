from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


EvaluationStrategy = Literal["all", "vector_only", "bm25_vector", "bm25_vector_graph"]


class EvaluationCreateRequest(BaseModel):
    name: str = Field(default="P0+ baseline", min_length=1, max_length=255)
    dataset_path: str = Field(default="evals/datasets/p0_plus_eval.jsonl", min_length=1)
    strategy: EvaluationStrategy = "all"
    repository_map: dict[str, str] = Field(default_factory=dict)
    top_k: int = Field(default=5, ge=1, le=20)


class EvaluationMetricResponse(BaseModel):
    strategy: str
    sample_count: int
    hit_at_5: float
    mrr: float
    citation_coverage: float
    avg_latency_ms: float
    p50_latency_ms: int
    p95_latency_ms: int
    avg_token_count: float
    token_estimated: bool
    token_estimated_count: int
    error_count: int


class EvaluationResultResponse(BaseModel):
    id: str
    sample_id: str
    sample_type: str
    repository_key: str
    strategy: str
    hit_at_5: bool
    mrr: float
    citation_coverage: float
    latency_ms: int
    token_count: int
    token_estimated: bool
    matched_files: list[str]
    matched_symbols: list[str]
    citations: list[dict[str, object]]
    error_message: str | None


class EvaluationRunResponse(BaseModel):
    run_id: str
    name: str
    dataset_path: str
    strategy: str
    status: str
    sample_count: int
    repository_map: dict[str, str]
    metrics: list[EvaluationMetricResponse]
    results: list[EvaluationResultResponse]
    warnings: list[str]
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class EvaluationRunSummary(BaseModel):
    run_id: str
    name: str
    dataset_path: str
    strategy: str
    status: str
    sample_count: int
    metrics: list[EvaluationMetricResponse]
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

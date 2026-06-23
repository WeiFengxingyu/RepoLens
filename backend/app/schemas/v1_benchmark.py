from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class V1BenchmarkCreateRequest(BaseModel):
    name: str = Field(default="V1 benchmark", min_length=1, max_length=255)
    dataset_path: str = Field(default="evals/datasets/v1_pr_mr_benchmark.jsonl", min_length=1)
    repository_map: dict[str, str] = Field(default_factory=dict)
    include_review: bool = True
    include_multi_agent: bool = True
    include_mcp: bool = True
    top_k: int = Field(default=5, ge=1, le=20)


class V1BenchmarkSampleResult(BaseModel):
    sample_id: str
    repository_key: str
    platform: str
    change_type: str
    title: str
    review: dict[str, Any] | None
    multi_agent: dict[str, Any] | None
    mcp: list[dict[str, Any]]
    errors: list[str]


class V1BenchmarkResponse(BaseModel):
    run_id: str
    name: str
    dataset_path: str
    status: str
    sample_count: int
    repository_map: dict[str, str]
    metrics: dict[str, Any]
    results: list[V1BenchmarkSampleResult]
    warnings: list[str]
    report_markdown: str
    created_at: datetime
    completed_at: datetime

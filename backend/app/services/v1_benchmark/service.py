from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Repository, RepositoryStatus, ToolCall
from app.schemas import ReviewCreateRequest
from app.schemas.multi_agent import MultiAgentReviewCreateRequest
from app.schemas.v1_benchmark import (
    V1BenchmarkCreateRequest,
    V1BenchmarkResponse,
    V1BenchmarkSampleResult,
)
from app.services.mcp import MCPService
from app.services.multi_agent import MultiAgentReviewService
from app.services.review import ReviewService
from app.services.v1_benchmark.dataset import (
    V1BenchmarkDatasetError,
    V1BenchmarkMCPToolCall,
    V1BenchmarkSample,
    load_v1_benchmark_dataset,
)
from app.services.v1_benchmark.metrics import (
    V1BenchmarkMCPSampleMetrics,
    V1BenchmarkMultiAgentSampleMetrics,
    V1BenchmarkReviewSampleMetrics,
    aggregate_mcp_metrics,
    aggregate_multi_agent_metrics,
    aggregate_review_metrics,
    compute_mcp_sample_metrics,
    compute_multi_agent_sample_metrics,
    compute_review_sample_metrics,
)


class V1BenchmarkServiceError(ValueError):
    pass


class V1BenchmarkValidationError(V1BenchmarkServiceError):
    pass


class V1BenchmarkRepositoryNotReadyError(V1BenchmarkServiceError):
    pass


class V1BenchmarkService:
    def __init__(self, db: Session):
        self.db = db

    def create_and_run(
        self,
        request: V1BenchmarkCreateRequest,
        settings: Settings,
    ) -> V1BenchmarkResponse:
        dataset = self._load_dataset(request.dataset_path)
        repositories = self._repositories_for_dataset(dataset.samples, request.repository_map)
        run_id = str(uuid4())
        created_at = datetime.utcnow()

        review_metrics: list[V1BenchmarkReviewSampleMetrics] = []
        multi_agent_metrics: list[V1BenchmarkMultiAgentSampleMetrics] = []
        mcp_metrics: list[V1BenchmarkMCPSampleMetrics] = []
        results: list[V1BenchmarkSampleResult] = []
        warnings: list[str] = []
        review_error_count = 0
        multi_agent_error_count = 0

        for sample in dataset.samples:
            repository = repositories[sample.repository_key]
            errors: list[str] = []
            review_payload: dict[str, Any] | None = None
            review_sample_metrics: V1BenchmarkReviewSampleMetrics | None = None
            review_latency = 0

            if request.include_review:
                review_payload, review_sample_metrics, review_latency, review_error = self._run_review_sample(
                    sample,
                    repository,
                    settings,
                    top_k=request.top_k,
                )
                review_metrics.append(review_sample_metrics)
                if review_error:
                    review_error_count += 1
                    errors.append(review_error)

            multi_payload = None
            multi_sample_metrics = None
            if request.include_multi_agent:
                multi_payload, multi_sample_metrics, multi_error = self._run_multi_agent_sample(
                    sample,
                    repository,
                    settings,
                    top_k=request.top_k,
                    single_review_token_count=review_sample_metrics.token_count
                    if review_sample_metrics
                    else 1,
                )
                multi_agent_metrics.append(multi_sample_metrics)
                if multi_error:
                    multi_agent_error_count += 1
                    errors.append(multi_error)

            sample_mcp_metrics: list[V1BenchmarkMCPSampleMetrics] = []
            if request.include_mcp:
                for expected_call in sample.mcp_tool_calls:
                    metric = self._run_mcp_tool_call(sample, repository, expected_call, settings)
                    sample_mcp_metrics.append(metric)
                    mcp_metrics.append(metric)

            results.append(
                V1BenchmarkSampleResult(
                    sample_id=sample.id,
                    repository_key=sample.repository_key,
                    platform=sample.platform,
                    change_type=sample.change_type,
                    title=sample.title,
                    review=review_sample_metrics.to_dict() if review_sample_metrics else None,
                    multi_agent=multi_sample_metrics.to_dict() if multi_sample_metrics else None,
                    mcp=[metric.to_dict() for metric in sample_mcp_metrics],
                    errors=errors,
                )
            )
            if review_latency > 3000:
                warnings.append(f"{sample.id}: single-main review latency exceeded 3000 ms.")

        metrics = {
            "review": aggregate_review_metrics(
                review_metrics,
                error_count=review_error_count,
            ).to_dict()
            if request.include_review
            else None,
            "multi_agent": aggregate_multi_agent_metrics(
                multi_agent_metrics,
                error_count=multi_agent_error_count,
            ).to_dict()
            if request.include_multi_agent
            else None,
            "mcp": aggregate_mcp_metrics(mcp_metrics).to_dict() if request.include_mcp else None,
        }
        completed_at = datetime.utcnow()
        return V1BenchmarkResponse(
            run_id=run_id,
            name=request.name,
            dataset_path=str(Path(request.dataset_path)),
            status="completed",
            sample_count=dataset.sample_count,
            repository_map=request.repository_map,
            metrics=metrics,
            results=results,
            warnings=warnings,
            report_markdown=_report_markdown(metrics, dataset.sample_count),
            created_at=created_at,
            completed_at=completed_at,
        )

    def _load_dataset(self, dataset_path: str):
        try:
            return load_v1_benchmark_dataset(_resolve_dataset_path(dataset_path))
        except V1BenchmarkDatasetError as exc:
            raise V1BenchmarkValidationError(str(exc)) from exc

    def _repositories_for_dataset(
        self,
        samples: list[V1BenchmarkSample],
        repository_map: dict[str, str],
    ) -> dict[str, Repository]:
        required_keys = sorted({sample.repository_key for sample in samples})
        missing_keys = [key for key in required_keys if key not in repository_map]
        if missing_keys:
            raise V1BenchmarkValidationError(
                "repository_map missing keys: " + ", ".join(missing_keys)
            )

        repositories: dict[str, Repository] = {}
        for repository_key in required_keys:
            repository_id = repository_map[repository_key]
            repository = self.db.get(Repository, repository_id)
            if repository is None:
                raise V1BenchmarkValidationError(
                    f"Repository for key '{repository_key}' was not found."
                )
            if repository.status != RepositoryStatus.READY.value:
                raise V1BenchmarkRepositoryNotReadyError(
                    f"Repository for key '{repository_key}' must be ready before V1 benchmark."
                )
            repositories[repository_key] = repository
        return repositories

    def _run_review_sample(
        self,
        sample: V1BenchmarkSample,
        repository: Repository,
        settings: Settings,
        *,
        top_k: int,
    ) -> tuple[dict[str, Any], V1BenchmarkReviewSampleMetrics, int, str | None]:
        service = ReviewService(self.db)
        request = ReviewCreateRequest(
            diff_text=sample.diff_text,
            top_k=top_k,
            use_bm25=True,
            use_vector=False,
            use_graph=True,
            run_static_check=False,
        )
        started = perf_counter()
        task = service.create_review_task(repository, request)
        task = service.run_review_task(task, request, settings)
        response = service.build_task_response(task).model_dump(mode="json")
        latency_ms = _elapsed_ms(started)
        error_message = response.get("error_message")
        metric = compute_review_sample_metrics(
            sample,
            response,
            latency_ms=latency_ms,
            error_message=str(error_message) if error_message else None,
        )
        return response, metric, latency_ms, str(error_message) if error_message else None

    def _run_multi_agent_sample(
        self,
        sample: V1BenchmarkSample,
        repository: Repository,
        settings: Settings,
        *,
        top_k: int,
        single_review_token_count: int,
    ) -> tuple[dict[str, Any], V1BenchmarkMultiAgentSampleMetrics, str | None]:
        service = MultiAgentReviewService(self.db)
        request = MultiAgentReviewCreateRequest(
            diff_text=sample.diff_text,
            top_k=top_k,
            use_bm25=True,
            use_vector=False,
            use_graph=True,
            run_static_check=False,
            round_limit=2,
            assignment_limit=8,
            token_budget=8000,
        )
        started = perf_counter()
        task = service.create_review_task(repository, request)
        task = service.run_review_task(task, request, settings)
        response = service.build_task_response(task).model_dump(mode="json")
        error_message = response.get("error_message")
        metric = compute_multi_agent_sample_metrics(
            sample,
            response,
            latency_ms=_elapsed_ms(started),
            single_review_token_count=single_review_token_count,
            error_message=str(error_message) if error_message else None,
        )
        return response, metric, str(error_message) if error_message else None

    def _run_mcp_tool_call(
        self,
        sample: V1BenchmarkSample,
        repository: Repository,
        expected_call: V1BenchmarkMCPToolCall,
        settings: Settings,
    ) -> V1BenchmarkMCPSampleMetrics:
        service = MCPService(self.db, settings)
        before = self._latest_tool_call_id()
        arguments = _replace_repository_placeholder(expected_call.arguments, repository.id)
        payload = {
            "jsonrpc": "2.0",
            "id": f"{sample.id}:{expected_call.tool_name}",
            "method": "tools/call",
            "params": {
                "name": expected_call.tool_name,
                "arguments": arguments,
                "client": {"name": "v1-benchmark"},
                "session_id": sample.id,
            },
        }
        started = perf_counter()
        response = service.handle_json_rpc(payload)
        latency_ms = _elapsed_ms(started)
        tool_call = self._latest_tool_call_after(before)
        actual_success = not bool(response.get("error")) and not bool(
            _dict_value(response.get("result")).get("isError")
        )
        permission = (
            tool_call.permission_decision
            if tool_call is not None
            else _permission_from_response(response)
        )
        error_message = None
        if response.get("error"):
            error_message = str(_dict_value(response.get("error")).get("message") or "MCP error")
        elif _dict_value(response.get("result")).get("isError"):
            error_message = "MCP tool returned isError."
        return compute_mcp_sample_metrics(
            expected_call,
            actual_success=actual_success,
            actual_permission_decision=permission,
            latency_ms=tool_call.latency_ms if tool_call and tool_call.latency_ms is not None else latency_ms,
            error_message=error_message,
        )

    def _latest_tool_call_id(self) -> str | None:
        tool_call = self.db.scalars(
            select(ToolCall).order_by(ToolCall.created_at.desc(), ToolCall.id.desc()).limit(1)
        ).first()
        return tool_call.id if tool_call else None

    def _latest_tool_call_after(self, previous_id: str | None) -> ToolCall | None:
        tool_call = self.db.scalars(
            select(ToolCall).order_by(ToolCall.created_at.desc(), ToolCall.id.desc()).limit(1)
        ).first()
        if tool_call is None or tool_call.id == previous_id:
            return None
        return tool_call


def _resolve_dataset_path(dataset_path: str) -> Path:
    path = Path(dataset_path)
    if path.exists() or path.is_absolute():
        return path
    repository_root = Path(__file__).resolve().parents[4]
    repository_relative = repository_root / path
    if repository_relative.exists():
        return repository_relative
    return path


def _replace_repository_placeholder(value: Any, repository_id: str) -> Any:
    if isinstance(value, str):
        return repository_id if value == "{repository_id}" else value
    if isinstance(value, list):
        return [_replace_repository_placeholder(item, repository_id) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_repository_placeholder(item, repository_id)
            for key, item in value.items()
        }
    return value


def _permission_from_response(response: dict[str, Any]) -> str | None:
    result = _dict_value(response.get("result"))
    structured = _dict_value(result.get("structuredContent"))
    decision = structured.get("permission_decision")
    return str(decision) if decision else None


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _elapsed_ms(started: float) -> int:
    return max(int((perf_counter() - started) * 1000), 0)


def _report_markdown(metrics: dict[str, Any], sample_count: int) -> str:
    review = _dict_value(metrics.get("review"))
    multi_agent = _dict_value(metrics.get("multi_agent"))
    mcp = _dict_value(metrics.get("mcp"))
    lines = [
        "# V1 Benchmark Report",
        "",
        f"- Samples: {sample_count}",
    ]
    if review:
        lines.extend(
            [
                f"- Review risk hit rate: {review.get('risk_hit_rate', 0)}",
                f"- Review citation coverage: {review.get('citation_coverage', 0)}",
                f"- Review unsupported claim rate: {review.get('unsupported_claim_rate', 0)}",
            ]
        )
    if multi_agent:
        lines.extend(
            [
                f"- Multi-Agent dissent usefulness: {multi_agent.get('dissent_usefulness', 0)}",
                f"- Multi-Agent arbiter resolution rate: {multi_agent.get('arbiter_resolution_rate', 0)}",
                f"- Multi-Agent token overhead ratio: {multi_agent.get('token_overhead_ratio', 0)}",
            ]
        )
    if mcp:
        lines.extend(
            [
                f"- MCP tool success rate: {mcp.get('tool_success_rate', 0)}",
                f"- MCP permission denial correctness: {mcp.get('permission_denial_correctness', 0)}",
            ]
        )
    return "\n".join(lines)

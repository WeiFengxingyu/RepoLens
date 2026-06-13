from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import EvaluationResult, EvaluationRun, EvaluationStatus, Repository
from app.schemas import (
    EvaluationCreateRequest,
    EvaluationMetricResponse,
    EvaluationResultResponse,
    EvaluationRunResponse,
    EvaluationRunSummary,
)
from app.services.evaluation.dataset import (
    EvaluationDatasetError,
    EvaluationSample,
    load_evaluation_dataset,
)
from app.services.evaluation.metrics import (
    EvaluationSampleMetric,
    compute_aggregate_metrics,
    compute_sample_metrics,
)
from app.services.evaluation.runner import (
    BM25_VECTOR_GRAPH_STRATEGY,
    BM25_VECTOR_STRATEGY,
    VECTOR_ONLY_STRATEGY,
    BM25VectorEvaluationResult,
    BM25VectorGraphEvaluationResult,
    VectorOnlyEvaluationResult,
    run_bm25_vector_graph_sample,
    run_bm25_vector_sample,
    run_vector_only_sample,
)


EVALUATION_STRATEGIES = [
    VECTOR_ONLY_STRATEGY,
    BM25_VECTOR_STRATEGY,
    BM25_VECTOR_GRAPH_STRATEGY,
]

EvaluationRunnerResult = (
    VectorOnlyEvaluationResult | BM25VectorEvaluationResult | BM25VectorGraphEvaluationResult
)


class EvaluationServiceError(ValueError):
    pass


class EvaluationRepositoryNotReadyError(EvaluationServiceError):
    pass


class EvaluationValidationError(EvaluationServiceError):
    pass


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db

    def create_and_run(
        self,
        request: EvaluationCreateRequest,
        settings: Settings,
    ) -> EvaluationRunResponse:
        dataset = self._load_dataset(request.dataset_path)
        strategies = _requested_strategies(request.strategy)
        repositories = self._repositories_for_dataset(dataset.samples, request.repository_map)

        run = EvaluationRun(
            name=request.name,
            dataset_path=str(Path(request.dataset_path)),
            strategy=request.strategy,
            status=EvaluationStatus.RUNNING.value,
            sample_count=dataset.sample_count,
            repository_map_json=json.dumps(request.repository_map, ensure_ascii=False),
            started_at=datetime.utcnow(),
        )
        self.db.add(run)
        self.db.flush()

        warnings: list[str] = []
        result_metrics: list[EvaluationSampleMetric] = []
        stored_results: list[EvaluationResult] = []

        for strategy in strategies:
            runner = _runner_for_strategy(strategy)
            strategy_metrics: list[EvaluationSampleMetric] = []
            for sample in dataset.samples:
                repository = repositories[sample.repository_key]
                runner_result = runner(
                    self.db,
                    sample,
                    repository_id=repository.id,
                    settings=settings,
                    top_k=request.top_k,
                )
                if runner_result.vector_disabled_reason:
                    warning = f"{strategy}:{sample.id}: {runner_result.vector_disabled_reason}"
                    if warning not in warnings:
                        warnings.append(warning)

                metric = compute_sample_metrics(sample, runner_result)
                result_metrics.append(metric)
                strategy_metrics.append(metric)
                stored_result = _stored_result(run.id, metric, runner_result)
                self.db.add(stored_result)
                stored_results.append(stored_result)

            run.metrics_json = json.dumps(
                [
                    *_loads_json_list(run.metrics_json),
                    compute_aggregate_metrics(strategy_metrics, strategy=strategy).to_dict(),
                ],
                ensure_ascii=False,
            )

        run.status = EvaluationStatus.COMPLETED.value
        run.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        for stored_result in stored_results:
            self.db.refresh(stored_result)

        return self.build_run_response(run, warnings=warnings)

    def list_runs(self) -> list[EvaluationRunSummary]:
        runs = self.db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc())).all()
        return [self.build_run_summary(run) for run in runs]

    def get_run(self, run_id: str) -> EvaluationRun | None:
        return self.db.get(EvaluationRun, run_id)

    def build_run_response(
        self,
        run: EvaluationRun,
        *,
        warnings: list[str] | None = None,
    ) -> EvaluationRunResponse:
        return EvaluationRunResponse(
            run_id=run.id,
            name=run.name,
            dataset_path=run.dataset_path,
            strategy=run.strategy,
            status=run.status,
            sample_count=run.sample_count,
            repository_map=_loads_json_dict(run.repository_map_json),
            metrics=[
                EvaluationMetricResponse(**metric)
                for metric in _loads_json_list(run.metrics_json)
            ],
            results=[_result_response(result) for result in run.results],
            warnings=warnings or [],
            error_message=run.error_message,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )

    def build_run_summary(self, run: EvaluationRun) -> EvaluationRunSummary:
        return EvaluationRunSummary(
            run_id=run.id,
            name=run.name,
            dataset_path=run.dataset_path,
            strategy=run.strategy,
            status=run.status,
            sample_count=run.sample_count,
            metrics=[
                EvaluationMetricResponse(**metric)
                for metric in _loads_json_list(run.metrics_json)
            ],
            error_message=run.error_message,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )

    def _load_dataset(self, dataset_path: str):
        try:
            return load_evaluation_dataset(_resolve_dataset_path(dataset_path))
        except EvaluationDatasetError as exc:
            raise EvaluationValidationError(str(exc)) from exc

    def _repositories_for_dataset(
        self,
        samples: list[EvaluationSample],
        repository_map: dict[str, str],
    ) -> dict[str, Repository]:
        required_keys = sorted({sample.repository_key for sample in samples})
        missing_keys = [key for key in required_keys if key not in repository_map]
        if missing_keys:
            raise EvaluationValidationError(
                "repository_map missing keys: " + ", ".join(missing_keys)
            )

        repositories: dict[str, Repository] = {}
        for repository_key in required_keys:
            repository_id = repository_map[repository_key]
            repository = self.db.get(Repository, repository_id)
            if repository is None:
                raise EvaluationValidationError(
                    f"Repository for key '{repository_key}' was not found."
                )
            if repository.status != "ready":
                raise EvaluationRepositoryNotReadyError(
                    f"Repository for key '{repository_key}' must be ready before evaluation."
                )
            repositories[repository_key] = repository
        return repositories


def _requested_strategies(strategy: str) -> list[str]:
    if strategy == "all":
        return list(EVALUATION_STRATEGIES)
    if strategy in EVALUATION_STRATEGIES:
        return [strategy]
    raise EvaluationValidationError(f"Unsupported evaluation strategy: {strategy}.")


def _resolve_dataset_path(dataset_path: str) -> Path:
    path = Path(dataset_path)
    if path.exists() or path.is_absolute():
        return path
    repository_root = Path(__file__).resolve().parents[4]
    repository_relative = repository_root / path
    if repository_relative.exists():
        return repository_relative
    return path


def _runner_for_strategy(strategy: str) -> Callable[..., EvaluationRunnerResult]:
    if strategy == VECTOR_ONLY_STRATEGY:
        return run_vector_only_sample
    if strategy == BM25_VECTOR_STRATEGY:
        return run_bm25_vector_sample
    if strategy == BM25_VECTOR_GRAPH_STRATEGY:
        return run_bm25_vector_graph_sample
    raise EvaluationValidationError(f"Unsupported evaluation strategy: {strategy}.")


def _stored_result(
    run_id: str,
    metric: EvaluationSampleMetric,
    runner_result: EvaluationRunnerResult,
) -> EvaluationResult:
    return EvaluationResult(
        run_id=run_id,
        sample_id=metric.sample_id,
        sample_type=metric.sample_type,
        repository_key=metric.repository_key,
        strategy=metric.strategy,
        hit_at_5=metric.hit_at_5,
        mrr=metric.mrr,
        citation_coverage=metric.citation_coverage,
        latency_ms=metric.latency_ms,
        token_count=metric.token_count,
        token_estimated=metric.token_estimated,
        matched_files_json=json.dumps(metric.matched_files, ensure_ascii=False),
        matched_symbols_json=json.dumps(metric.matched_symbols, ensure_ascii=False),
        citations_json=json.dumps(
            [evidence.to_dict() for evidence in runner_result.evidences],
            ensure_ascii=False,
        ),
        error_message=metric.error_message,
    )


def _result_response(result: EvaluationResult) -> EvaluationResultResponse:
    return EvaluationResultResponse(
        id=result.id,
        sample_id=result.sample_id,
        sample_type=result.sample_type,
        repository_key=result.repository_key,
        strategy=result.strategy,
        hit_at_5=result.hit_at_5,
        mrr=result.mrr,
        citation_coverage=result.citation_coverage,
        latency_ms=result.latency_ms,
        token_count=result.token_count,
        token_estimated=result.token_estimated,
        matched_files=_loads_json_str_list(result.matched_files_json),
        matched_symbols=_loads_json_str_list(result.matched_symbols_json),
        citations=_loads_json_dict_list(result.citations_json),
        error_message=result.error_message,
    )


def _loads_json_list(value: str | None) -> list[dict[str, Any]]:
    if not value:
        return []
    loaded = json.loads(value)
    return loaded if isinstance(loaded, list) else []


def _loads_json_dict(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        return {}
    return {str(key): str(item) for key, item in loaded.items()}


def _loads_json_str_list(value: str | None) -> list[str]:
    if not value:
        return []
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        return []
    return [str(item) for item in loaded]


def _loads_json_dict_list(value: str | None) -> list[dict[str, object]]:
    if not value:
        return []
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        return []
    return [dict(item) for item in loaded if isinstance(item, dict)]

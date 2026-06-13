from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import json
from pathlib import Path
from typing import Any


class EvaluationSampleType(StrEnum):
    LOCATION = "location"
    EXPLANATION = "explanation"
    ARCHITECTURE = "architecture"
    REVIEW = "review"


class EvaluationDatasetError(ValueError):
    """Raised when a Phase 5 evaluation dataset violates the schema."""


@dataclass(frozen=True)
class EvaluationSample:
    id: str
    type: EvaluationSampleType
    repository_key: str
    question: str
    expected_files: list[str]
    expected_symbols: list[str] = field(default_factory=list)
    expected_answer_keywords: list[str] = field(default_factory=list)
    review_diff: str | None = None
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.type.value,
            "repository_key": self.repository_key,
            "question": self.question,
            "expected_files": self.expected_files,
            "expected_symbols": self.expected_symbols,
            "expected_answer_keywords": self.expected_answer_keywords,
            "review_diff": self.review_diff,
            "tags": self.tags,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class EvaluationDataset:
    path: str
    samples: list[EvaluationSample]

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    def count_by_type(self) -> dict[str, int]:
        counts = {sample_type.value: 0 for sample_type in EvaluationSampleType}
        for sample in self.samples:
            counts[sample.type.value] += 1
        return counts


def load_evaluation_dataset(path: str | Path) -> EvaluationDataset:
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise EvaluationDatasetError(f"Evaluation dataset does not exist: {dataset_path}")
    if not dataset_path.is_file():
        raise EvaluationDatasetError(f"Evaluation dataset is not a file: {dataset_path}")

    samples: list[EvaluationSample] = []
    seen_ids: set[str] = set()
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                raw_sample = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluationDatasetError(
                    f"Line {line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(raw_sample, dict):
                raise EvaluationDatasetError(f"Line {line_number}: sample must be an object.")

            sample = parse_evaluation_sample(raw_sample, line_number=line_number)
            if sample.id in seen_ids:
                raise EvaluationDatasetError(f"Line {line_number}: duplicate sample id '{sample.id}'.")
            seen_ids.add(sample.id)
            samples.append(sample)

    if not samples:
        raise EvaluationDatasetError("Evaluation dataset cannot be empty.")

    return EvaluationDataset(path=str(dataset_path), samples=samples)


def parse_evaluation_sample(
    value: dict[str, Any],
    *,
    line_number: int | None = None,
) -> EvaluationSample:
    prefix = f"Line {line_number}: " if line_number is not None else ""
    sample_id = _required_str(value, "id", prefix=prefix)
    raw_type = _required_str(value, "type", prefix=prefix)
    try:
        sample_type = EvaluationSampleType(raw_type)
    except ValueError as exc:
        allowed = ", ".join(sample_type.value for sample_type in EvaluationSampleType)
        raise EvaluationDatasetError(
            f"{prefix}type must be one of: {allowed}."
        ) from exc

    repository_key = _required_str(value, "repository_key", prefix=prefix)
    question = _required_str(value, "question", prefix=prefix)
    expected_files = _string_list(value.get("expected_files"), field_name="expected_files", prefix=prefix)
    if not expected_files:
        raise EvaluationDatasetError(f"{prefix}expected_files must contain at least one item.")
    expected_files = [_normalize_eval_path(path, prefix=prefix) for path in expected_files]

    expected_symbols = _string_list(
        value.get("expected_symbols", []),
        field_name="expected_symbols",
        prefix=prefix,
    )
    expected_answer_keywords = _string_list(
        value.get("expected_answer_keywords", []),
        field_name="expected_answer_keywords",
        prefix=prefix,
    )
    tags = _string_list(value.get("tags", []), field_name="tags", prefix=prefix)
    notes = _optional_str(value.get("notes"), default="")
    review_diff = _optional_str(value.get("review_diff"), default=None)
    if sample_type == EvaluationSampleType.REVIEW and not review_diff:
        raise EvaluationDatasetError(f"{prefix}review samples require review_diff.")

    return EvaluationSample(
        id=sample_id,
        type=sample_type,
        repository_key=repository_key,
        question=question,
        expected_files=_deduplicate(expected_files),
        expected_symbols=_deduplicate(expected_symbols),
        expected_answer_keywords=_deduplicate(expected_answer_keywords),
        review_diff=review_diff,
        tags=_deduplicate(tags),
        notes=notes,
    )


def _required_str(value: dict[str, Any], field_name: str, *, prefix: str) -> str:
    raw_value = value.get(field_name)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise EvaluationDatasetError(f"{prefix}{field_name} is required.")
    return " ".join(raw_value.strip().split())


def _optional_str(value: Any, *, default: str | None) -> str | None:
    if value is None:
        return default
    if not isinstance(value, str):
        return default
    stripped = value.strip()
    return stripped or default


def _string_list(value: Any, *, field_name: str, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise EvaluationDatasetError(f"{prefix}{field_name} must be a list of strings.")
    items: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise EvaluationDatasetError(
                f"{prefix}{field_name}[{index}] must be a non-empty string."
            )
        items.append(" ".join(item.strip().split()))
    return items


def _normalize_eval_path(path_value: str, *, prefix: str) -> str:
    normalized = path_value.replace("\\", "/").strip()
    path = Path(normalized)
    if path.is_absolute() or normalized.startswith("/") or _has_windows_drive_prefix(normalized):
        raise EvaluationDatasetError(f"{prefix}expected_files cannot contain absolute paths.")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise EvaluationDatasetError(f"{prefix}expected_files cannot contain path traversal.")
    return normalized


def _has_windows_drive_prefix(path_value: str) -> bool:
    return (
        len(path_value) >= 3
        and path_value[1] == ":"
        and path_value[0].isalpha()
        and path_value[2] == "/"
    )


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated

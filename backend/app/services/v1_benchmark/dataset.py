from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


SUPPORTED_PLATFORMS = {
    "github",
    "gitee",
    "gitlab",
    "self_hosted_gitlab",
    "synthetic",
}
SUPPORTED_CHANGE_TYPES = {"pull_request", "merge_request"}
SUPPORTED_PERMISSION_DECISIONS = {"allow", "deny", "disabled", "confirm_required"}


class V1BenchmarkDatasetError(ValueError):
    """Raised when a Phase 9 V1 benchmark dataset violates the schema."""


@dataclass(frozen=True)
class V1BenchmarkExpectedRisk:
    title_keywords: list[str]
    severity: str
    file_path: str
    evidence_required: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "title_keywords": self.title_keywords,
            "severity": self.severity,
            "file_path": self.file_path,
            "evidence_required": self.evidence_required,
        }


@dataclass(frozen=True)
class V1BenchmarkMCPToolCall:
    tool_name: str
    arguments: dict[str, Any]
    expect_success: bool
    expect_permission_decision: str

    def to_dict(self) -> dict[str, object]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "expect_success": self.expect_success,
            "expect_permission_decision": self.expect_permission_decision,
        }


@dataclass(frozen=True)
class V1BenchmarkSample:
    id: str
    repository_key: str
    platform: str
    change_type: str
    url: str
    title: str
    diff_text: str
    expected_risks: list[V1BenchmarkExpectedRisk]
    expected_files: list[str]
    expected_labels: list[str] = field(default_factory=list)
    mcp_tool_calls: list[V1BenchmarkMCPToolCall] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "repository_key": self.repository_key,
            "platform": self.platform,
            "change_type": self.change_type,
            "url": self.url,
            "title": self.title,
            "diff_text": self.diff_text,
            "expected_risks": [risk.to_dict() for risk in self.expected_risks],
            "expected_files": self.expected_files,
            "expected_labels": self.expected_labels,
            "mcp_tool_calls": [call.to_dict() for call in self.mcp_tool_calls],
            "notes": self.notes,
        }


@dataclass(frozen=True)
class V1BenchmarkDataset:
    path: str
    samples: list[V1BenchmarkSample]

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    def count_by_platform(self) -> dict[str, int]:
        counts = {platform: 0 for platform in sorted(SUPPORTED_PLATFORMS)}
        for sample in self.samples:
            counts[sample.platform] += 1
        return counts


def load_v1_benchmark_dataset(path: str | Path) -> V1BenchmarkDataset:
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise V1BenchmarkDatasetError(f"V1 benchmark dataset does not exist: {dataset_path}")
    if not dataset_path.is_file():
        raise V1BenchmarkDatasetError(f"V1 benchmark dataset is not a file: {dataset_path}")

    samples: list[V1BenchmarkSample] = []
    seen_ids: set[str] = set()
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                raw_sample = json.loads(line)
            except json.JSONDecodeError as exc:
                raise V1BenchmarkDatasetError(
                    f"Line {line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(raw_sample, dict):
                raise V1BenchmarkDatasetError(f"Line {line_number}: sample must be an object.")
            sample = parse_v1_benchmark_sample(raw_sample, line_number=line_number)
            if sample.id in seen_ids:
                raise V1BenchmarkDatasetError(
                    f"Line {line_number}: duplicate sample id '{sample.id}'."
                )
            seen_ids.add(sample.id)
            samples.append(sample)

    if not samples:
        raise V1BenchmarkDatasetError("V1 benchmark dataset cannot be empty.")
    if len(samples) < 20:
        raise V1BenchmarkDatasetError("V1 benchmark dataset must contain at least 20 samples.")
    return V1BenchmarkDataset(path=str(dataset_path), samples=samples)


def parse_v1_benchmark_sample(
    value: dict[str, Any],
    *,
    line_number: int | None = None,
) -> V1BenchmarkSample:
    prefix = f"Line {line_number}: " if line_number is not None else ""
    sample_id = _required_str(value, "id", prefix=prefix)
    repository_key = _required_str(value, "repository_key", prefix=prefix)
    platform = _required_str(value, "platform", prefix=prefix)
    if platform not in SUPPORTED_PLATFORMS:
        raise V1BenchmarkDatasetError(
            f"{prefix}platform must be one of: {', '.join(sorted(SUPPORTED_PLATFORMS))}."
        )
    change_type = _required_str(value, "change_type", prefix=prefix)
    if change_type not in SUPPORTED_CHANGE_TYPES:
        raise V1BenchmarkDatasetError(
            f"{prefix}change_type must be one of: {', '.join(sorted(SUPPORTED_CHANGE_TYPES))}."
        )
    url = _required_str(value, "url", prefix=prefix)
    title = _required_str(value, "title", prefix=prefix)
    diff_text = _required_multiline_str(value, "diff_text", prefix=prefix)
    expected_files = _normalized_path_list(value.get("expected_files"), "expected_files", prefix)
    if not expected_files:
        raise V1BenchmarkDatasetError(f"{prefix}expected_files must contain at least one item.")
    expected_risks = _expected_risks(value.get("expected_risks"), prefix=prefix)
    if not expected_risks:
        raise V1BenchmarkDatasetError(f"{prefix}expected_risks must contain at least one item.")

    return V1BenchmarkSample(
        id=sample_id,
        repository_key=repository_key,
        platform=platform,
        change_type=change_type,
        url=url,
        title=title,
        diff_text=diff_text,
        expected_risks=expected_risks,
        expected_files=_deduplicate(expected_files),
        expected_labels=_deduplicate(
            _string_list(value.get("expected_labels", []), "expected_labels", prefix)
        ),
        mcp_tool_calls=_mcp_tool_calls(value.get("mcp_tool_calls", []), prefix=prefix),
        notes=_optional_str(value.get("notes"), default=""),
    )


def _expected_risks(value: Any, *, prefix: str) -> list[V1BenchmarkExpectedRisk]:
    if not isinstance(value, list):
        raise V1BenchmarkDatasetError(f"{prefix}expected_risks must be a list.")
    risks = []
    for index, item in enumerate(value, start=1):
        item_prefix = f"{prefix}expected_risks[{index}]: "
        if not isinstance(item, dict):
            raise V1BenchmarkDatasetError(f"{item_prefix}must be an object.")
        keywords = _string_list(item.get("title_keywords"), "title_keywords", item_prefix)
        if not keywords:
            raise V1BenchmarkDatasetError(f"{item_prefix}title_keywords cannot be empty.")
        risks.append(
            V1BenchmarkExpectedRisk(
                title_keywords=_deduplicate([keyword.lower() for keyword in keywords]),
                severity=_required_str(item, "severity", prefix=item_prefix),
                file_path=_normalize_path(_required_str(item, "file_path", prefix=item_prefix), item_prefix),
                evidence_required=_bool_value(item.get("evidence_required"), default=True),
            )
        )
    return risks


def _mcp_tool_calls(value: Any, *, prefix: str) -> list[V1BenchmarkMCPToolCall]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise V1BenchmarkDatasetError(f"{prefix}mcp_tool_calls must be a list.")
    calls = []
    for index, item in enumerate(value, start=1):
        item_prefix = f"{prefix}mcp_tool_calls[{index}]: "
        if not isinstance(item, dict):
            raise V1BenchmarkDatasetError(f"{item_prefix}must be an object.")
        arguments = item.get("arguments", {})
        if not isinstance(arguments, dict):
            raise V1BenchmarkDatasetError(f"{item_prefix}arguments must be an object.")
        decision = _required_str(item, "expect_permission_decision", prefix=item_prefix)
        if decision not in SUPPORTED_PERMISSION_DECISIONS:
            raise V1BenchmarkDatasetError(
                f"{item_prefix}expect_permission_decision must be one of: "
                f"{', '.join(sorted(SUPPORTED_PERMISSION_DECISIONS))}."
            )
        calls.append(
            V1BenchmarkMCPToolCall(
                tool_name=_required_str(item, "tool_name", prefix=item_prefix),
                arguments=dict(arguments),
                expect_success=_bool_value(item.get("expect_success"), default=True),
                expect_permission_decision=decision,
            )
        )
    return calls


def _required_str(value: dict[str, Any], field_name: str, *, prefix: str) -> str:
    raw_value = value.get(field_name)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise V1BenchmarkDatasetError(f"{prefix}{field_name} is required.")
    return " ".join(raw_value.strip().split())


def _required_multiline_str(value: dict[str, Any], field_name: str, *, prefix: str) -> str:
    raw_value = value.get(field_name)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise V1BenchmarkDatasetError(f"{prefix}{field_name} is required.")
    return raw_value.strip()


def _optional_str(value: Any, *, default: str) -> str:
    if not isinstance(value, str):
        return default
    return value.strip() or default


def _string_list(value: Any, field_name: str, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise V1BenchmarkDatasetError(f"{prefix}{field_name} must be a list of strings.")
    items: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise V1BenchmarkDatasetError(
                f"{prefix}{field_name}[{index}] must be a non-empty string."
            )
        items.append(" ".join(item.strip().split()))
    return items


def _normalized_path_list(value: Any, field_name: str, prefix: str) -> list[str]:
    return [_normalize_path(path_value, prefix) for path_value in _string_list(value, field_name, prefix)]


def _normalize_path(path_value: str, prefix: str) -> str:
    normalized = path_value.replace("\\", "/").strip()
    path = Path(normalized)
    if path.is_absolute() or normalized.startswith("/") or _has_windows_drive_prefix(normalized):
        raise V1BenchmarkDatasetError(f"{prefix}paths cannot be absolute.")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise V1BenchmarkDatasetError(f"{prefix}paths cannot contain traversal.")
    return normalized


def _has_windows_drive_prefix(path_value: str) -> bool:
    return (
        len(path_value) >= 3
        and path_value[1] == ":"
        and path_value[0].isalpha()
        and path_value[2] == "/"
    )


def _bool_value(value: Any, *, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated

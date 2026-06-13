import json
from pathlib import Path

import pytest

from app.services.evaluation import (
    EvaluationDatasetError,
    EvaluationSampleType,
    load_evaluation_dataset,
    parse_evaluation_sample,
)


def test_load_evaluation_dataset_parses_valid_jsonl(tmp_path: Path) -> None:
    dataset_path = tmp_path / "p0_plus_eval.jsonl"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "qa-location-001",
                "type": "location",
                "repository_key": "python_demo",
                "question": "Where is import implemented?",
                "expected_files": ["app/service.py", "app/service.py"],
                "expected_symbols": ["RepositoryService", "RepositoryService"],
                "expected_answer_keywords": ["import"],
                "tags": ["qa", "retrieval", "qa"],
                "notes": "location sample",
            },
            {
                "id": "review-risk-001",
                "type": "review",
                "repository_key": "python_demo",
                "question": "Review this diff.",
                "expected_files": ["app/auth.py"],
                "expected_symbols": ["validate_token"],
                "review_diff": "diff --git a/app/auth.py b/app/auth.py\n--- a/app/auth.py\n+++ b/app/auth.py",
            },
        ],
    )

    dataset = load_evaluation_dataset(dataset_path)

    assert dataset.path == str(dataset_path)
    assert dataset.sample_count == 2
    assert dataset.count_by_type()["location"] == 1
    assert dataset.count_by_type()["review"] == 1
    first = dataset.samples[0]
    assert first.type == EvaluationSampleType.LOCATION
    assert first.expected_files == ["app/service.py"]
    assert first.expected_symbols == ["RepositoryService"]
    assert first.tags == ["qa", "retrieval"]
    assert first.to_dict()["type"] == "location"


def test_parse_evaluation_sample_normalizes_path_and_strings() -> None:
    sample = parse_evaluation_sample(
        {
            "id": " qa-explain-001 ",
            "type": "explanation",
            "repository_key": " ts_demo ",
            "question": "  Explain   the hook. ",
            "expected_files": ["src\\hooks\\useRepo.ts"],
        }
    )

    assert sample.id == "qa-explain-001"
    assert sample.repository_key == "ts_demo"
    assert sample.question == "Explain the hook."
    assert sample.expected_files == ["src/hooks/useRepo.ts"]


def test_review_sample_requires_review_diff() -> None:
    with pytest.raises(EvaluationDatasetError, match="review samples require review_diff"):
        parse_evaluation_sample(
            {
                "id": "review-risk-001",
                "type": "review",
                "repository_key": "python_demo",
                "question": "Review this diff.",
                "expected_files": ["app/auth.py"],
            }
        )


def test_dataset_rejects_duplicate_ids(tmp_path: Path) -> None:
    dataset_path = tmp_path / "duplicate.jsonl"
    _write_jsonl(
        dataset_path,
        [
            _sample("qa-location-001"),
            _sample("qa-location-001"),
        ],
    )

    with pytest.raises(EvaluationDatasetError, match="duplicate sample id"):
        load_evaluation_dataset(dataset_path)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "id": "bad-type",
                "type": "unknown",
                "repository_key": "python_demo",
                "question": "Where is the service?",
                "expected_files": ["app/service.py"],
            },
            "type must be one of",
        ),
        (
            {
                "id": "missing-files",
                "type": "location",
                "repository_key": "python_demo",
                "question": "Where is the service?",
                "expected_files": [],
            },
            "expected_files must contain",
        ),
        (
            {
                "id": "bad-files",
                "type": "location",
                "repository_key": "python_demo",
                "question": "Where is the service?",
                "expected_files": "app.py",
            },
            "expected_files must be a list",
        ),
        (
            {
                "id": "bad-tags",
                "type": "location",
                "repository_key": "python_demo",
                "question": "Where is the service?",
                "expected_files": ["app/service.py"],
                "tags": ["qa", ""],
            },
            "tags\\[2\\]",
        ),
    ],
)
def test_parse_evaluation_sample_rejects_invalid_payload(
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(EvaluationDatasetError, match=message):
        parse_evaluation_sample(payload)


@pytest.mark.parametrize(
    "path_value",
    [
        "../secret.py",
        "app/../secret.py",
        "/absolute/path.py",
        "C:/absolute/path.py",
    ],
)
def test_parse_evaluation_sample_rejects_unsafe_expected_files(path_value: str) -> None:
    with pytest.raises(EvaluationDatasetError, match="expected_files"):
        parse_evaluation_sample({**_sample("unsafe-path"), "expected_files": [path_value]})


def test_load_evaluation_dataset_rejects_invalid_json_and_empty_dataset(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.jsonl"
    invalid_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(EvaluationDatasetError, match="invalid JSON"):
        load_evaluation_dataset(invalid_path)

    empty_path = tmp_path / "empty.jsonl"
    empty_path.write_text("\n", encoding="utf-8")
    with pytest.raises(EvaluationDatasetError, match="cannot be empty"):
        load_evaluation_dataset(empty_path)


def test_load_evaluation_dataset_rejects_missing_or_directory(tmp_path: Path) -> None:
    with pytest.raises(EvaluationDatasetError, match="does not exist"):
        load_evaluation_dataset(tmp_path / "missing.jsonl")

    with pytest.raises(EvaluationDatasetError, match="not a file"):
        load_evaluation_dataset(tmp_path)


def _sample(sample_id: str) -> dict[str, object]:
    return {
        "id": sample_id,
        "type": "location",
        "repository_key": "python_demo",
        "question": "Where is the service?",
        "expected_files": ["app/service.py"],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )

from pathlib import Path

from app.services.evaluation import EvaluationSampleType, load_evaluation_dataset


REPO_ROOT = Path(__file__).resolve().parents[3]
P0_PLUS_DATASET = REPO_ROOT / "evals" / "datasets" / "p0_plus_eval.jsonl"


def test_p0_plus_eval_dataset_has_required_distribution() -> None:
    dataset = load_evaluation_dataset(P0_PLUS_DATASET)

    assert dataset.sample_count == 50
    assert dataset.count_by_type() == {
        "location": 20,
        "explanation": 10,
        "architecture": 10,
        "review": 10,
    }


def test_p0_plus_eval_dataset_covers_demo_repositories_and_symbols() -> None:
    dataset = load_evaluation_dataset(P0_PLUS_DATASET)

    repository_keys = {sample.repository_key for sample in dataset.samples}
    assert repository_keys == {"python_demo", "ts_demo"}
    assert sum(1 for sample in dataset.samples if sample.expected_symbols) >= 30
    assert all(sample.expected_files for sample in dataset.samples)
    assert all(sample.question for sample in dataset.samples)


def test_p0_plus_eval_review_samples_have_unified_diffs() -> None:
    dataset = load_evaluation_dataset(P0_PLUS_DATASET)

    review_samples = [
        sample for sample in dataset.samples if sample.type == EvaluationSampleType.REVIEW
    ]
    assert len(review_samples) == 10
    assert all(sample.review_diff for sample in review_samples)
    assert all(sample.review_diff and sample.review_diff.startswith("diff --git ") for sample in review_samples)
    assert all("--- " in (sample.review_diff or "") for sample in review_samples)
    assert all("+++ " in (sample.review_diff or "") for sample in review_samples)


def test_p0_plus_eval_ids_are_grouped_and_unique() -> None:
    dataset = load_evaluation_dataset(P0_PLUS_DATASET)

    ids = [sample.id for sample in dataset.samples]
    assert len(ids) == len(set(ids))
    assert ids[:20] == [f"loc-{index:03d}" for index in range(1, 21)]
    assert ids[20:30] == [f"exp-{index:03d}" for index in range(1, 11)]
    assert ids[30:40] == [f"arch-{index:03d}" for index in range(1, 11)]
    assert ids[40:] == [f"review-{index:03d}" for index in range(1, 11)]

from pathlib import Path

from app.services.evaluation import load_evaluation_dataset


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "evals" / "datasets" / "p0_plus_eval.jsonl"
DEMO_ROOT = REPO_ROOT / "evals" / "demo_repos"
PYTHON_DEMO = DEMO_ROOT / "python_service"
TS_DEMO = DEMO_ROOT / "ts_webapp"


def test_phase5_demo_repositories_exist_and_match_dataset_files() -> None:
    dataset = load_evaluation_dataset(DATASET_PATH)
    repo_paths = {"python_demo": PYTHON_DEMO, "ts_demo": TS_DEMO}

    for repository_key, repo_path in repo_paths.items():
        assert repo_path.is_dir()
        expected_files = {
            file_path
            for sample in dataset.samples
            if sample.repository_key == repository_key
            for file_path in sample.expected_files
        }
        missing = [file_path for file_path in sorted(expected_files) if not (repo_path / file_path).is_file()]
        assert missing == []


def test_phase5_demo_repositories_are_small_and_safe() -> None:
    for repo_path in [PYTHON_DEMO, TS_DEMO]:
        files = [path for path in repo_path.rglob("*") if path.is_file()]
        assert 20 <= len(files) <= 60
        assert all(".env" not in path.name for path in files)
        assert all(path.stat().st_size < 20_000 for path in files)


def test_phase5_python_demo_contains_expected_backend_layers() -> None:
    required = [
        "app/api/tasks.py",
        "app/services/tasks.py",
        "app/repositories/tasks.py",
        "app/auth/tokens.py",
        "app/billing/invoices.py",
        "tests/test_billing.py",
    ]

    assert all((PYTHON_DEMO / path).is_file() for path in required)


def test_phase5_ts_demo_contains_expected_frontend_layers() -> None:
    required = [
        "src/app/dashboard/page.tsx",
        "src/components/repository-list.tsx",
        "src/components/evaluation-panel.tsx",
        "src/hooks/use-evaluation.ts",
        "src/lib/repositories.ts",
        "tests/persistence.test.ts",
    ]

    assert all((TS_DEMO / path).is_file() for path in required)

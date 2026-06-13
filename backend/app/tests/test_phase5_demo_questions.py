import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
QUESTIONS_JSON = REPO_ROOT / "evals" / "datasets" / "demo_questions.json"
QUESTIONS_MD = REPO_ROOT / "evals" / "demo_questions.md"
DEMO_ROOT = REPO_ROOT / "evals" / "demo_repos"


def test_phase5_demo_questions_have_required_distribution_and_fields() -> None:
    questions = _load_questions()

    assert len(questions) == 10
    assert {question["category"] for question in questions} == {
        "architecture",
        "location",
        "explanation",
        "impact",
        "review",
    }
    assert {question["repository_key"] for question in questions} == {"python_demo", "ts_demo"}

    for question in questions:
        assert question["id"].startswith("demo-")
        assert question["question"].strip()
        assert question["expected_answer_focus"]
        assert question["suggested_demo_flow"]
        assert question["screenshot_target"] in {
            "repository-status",
            "evidence-panel",
            "ask-trace-panel",
            "review-panel",
            "evaluation-panel",
        }


def test_phase5_demo_questions_reference_existing_demo_files() -> None:
    questions = _load_questions()

    for question in questions:
        repo_path = DEMO_ROOT / _repo_dir(question["repository_key"])
        assert repo_path.is_dir()
        missing = [
            file_path
            for file_path in question["expected_files"]
            if not (repo_path / file_path).is_file()
        ]
        assert missing == []


def test_phase5_demo_review_questions_have_unified_diffs() -> None:
    questions = _load_questions()
    reviewish = [
        question
        for question in questions
        if question["category"] in {"impact", "review"}
    ]

    assert len(reviewish) == 4
    assert all(question["review_diff"] for question in reviewish)
    assert all(question["review_diff"].startswith("diff --git ") for question in reviewish)
    assert all("--- " in question["review_diff"] for question in reviewish)
    assert all("+++ " in question["review_diff"] for question in reviewish)


def test_phase5_demo_questions_markdown_matches_json_ids() -> None:
    questions = _load_questions()
    markdown = QUESTIONS_MD.read_text(encoding="utf-8")

    assert "Demo Flow" in markdown
    assert "Screenshot Mapping" in markdown
    for question in questions:
        assert question["id"] in markdown


def _load_questions() -> list[dict[str, object]]:
    return json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))


def _repo_dir(repository_key: str) -> str:
    if repository_key == "python_demo":
        return "python_service"
    if repository_key == "ts_demo":
        return "ts_webapp"
    raise AssertionError(f"Unexpected repository key {repository_key}")

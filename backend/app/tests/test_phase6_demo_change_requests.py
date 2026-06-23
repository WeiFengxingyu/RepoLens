import json
from pathlib import Path
from time import perf_counter

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import DEFAULT_CHANGE_REQUEST_MAX_DIFF_CHARS
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import ChangeRequest, CodeChunk, CodeLanguage, Repository, RepositoryStatus, SymbolType, TaskStatus
from app.services.change_request import (
    CHANGE_TYPE_PULL_REQUEST,
    PLATFORM_GITHUB,
    ChangeRequestCommit,
    ChangeRequestFile,
    ChangeRequestRef,
    UnsupportedChangeRequestProviderError,
    parse_change_request_url,
)
from app.services.change_request.models import ChangeRequest as FetchedChangeRequest


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = REPO_ROOT / "evals" / "change_requests" / "phase6_demo_prs.json"


def test_phase6_demo_change_request_fixture_is_small_safe_and_parseable() -> None:
    fixtures = _load_fixtures()

    assert len(fixtures) == 1
    fixture = fixtures[0]
    assert fixture["id"] == "phase6-cr-001"
    assert fixture["repository_key"] == "ts_demo"
    assert fixture["repository_path"] == "evals/demo_repos/ts_webapp"
    assert fixture["platform"] == PLATFORM_GITHUB
    assert fixture["change_type"] == CHANGE_TYPE_PULL_REQUEST

    ref = parse_change_request_url(fixture["url"])

    assert ref.platform == PLATFORM_GITHUB
    assert ref.change_type == CHANGE_TYPE_PULL_REQUEST
    assert ref.owner == fixture["owner"]
    assert ref.repo == fixture["repo"]
    assert ref.number == fixture["number"]
    assert len(fixture["diff_text"]) < DEFAULT_CHANGE_REQUEST_MAX_DIFF_CHARS
    assert "token" not in json.dumps(fixture).lower()
    assert "authorization" not in json.dumps(fixture).lower()


def test_phase6_demo_change_request_diff_references_existing_files() -> None:
    fixture = _load_fixtures()[0]
    repository_path = REPO_ROOT / fixture["repository_path"]

    assert repository_path.is_dir()
    assert fixture["diff_text"].startswith("diff --git ")
    assert "--- " in fixture["diff_text"]
    assert "+++ " in fixture["diff_text"]
    for file_path in fixture["changed_files"]:
        assert (repository_path / file_path).is_file()
        assert f"b/{file_path}" in fixture["diff_text"]


def test_phase6_demo_change_request_has_review_demo_expectations() -> None:
    fixture = _load_fixtures()[0]

    assert fixture["expected_review_focus"] == [
        "Whitespace-only diff can now be submitted",
        "Button disabled condition and submit guard diverge",
        "Add a UI test for whitespace-only diff input",
    ]
    assert fixture["expected_tool_calls"] == ["analyze_diff", "code_search"]
    assert fixture["expected_metadata"] == {
        "changed_file_count": 1,
        "addition_count": 1,
        "deletion_count": 1,
        "commit_count": 1,
    }


def test_phase6_demo_change_request_includes_unsupported_provider_failure_url() -> None:
    fixture = _load_fixtures()[0]

    try:
        parse_change_request_url(fixture["unsupported_provider_url"])
    except UnsupportedChangeRequestProviderError as exc:
        assert "Unsupported PR/MR provider" in str(exc)
    else:
        raise AssertionError("Unsupported provider URL should not be parseable in Phase 6.")


def test_phase6_demo_change_request_can_drive_review_api(monkeypatch) -> None:
    fixture = _load_fixtures()[0]
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository = Repository(
            name="ts_demo",
            source_type="local",
            local_path=str(REPO_ROOT / fixture["repository_path"]),
            status=RepositoryStatus.READY.value,
        )
        db.add(repository)
        db.commit()
        repository_id = repository.id

    provider = FixtureProvider(fixture)
    monkeypatch.setattr(
        "app.services.change_request.service.choose_change_request_provider",
        lambda url: provider,
    )
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={"url": fixture["url"], "use_vector": False},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["change_request"]["platform"] == PLATFORM_GITHUB
    assert body["change_request"]["title"] == fixture["title"]
    assert body["change_request"]["changed_file_count"] == 1
    assert body["review"]["status"] == TaskStatus.COMPLETED.value
    assert [tool_call["tool_name"] for tool_call in body["review"]["tool_calls"]] == [
        "analyze_diff",
        "code_search",
    ]


def test_phase6_demo_change_request_smoke_records_metrics_citations_and_safety(monkeypatch) -> None:
    fixture = _load_fixtures()[0]
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository = Repository(
            name="ts_demo",
            source_type="local",
            local_path=str(REPO_ROOT / fixture["repository_path"]),
            status=RepositoryStatus.READY.value,
            file_count=1,
            parsed_file_count=1,
            chunk_count=1,
        )
        db.add(repository)
        db.flush()
        db.add(_review_panel_chunk(repository.id, fixture))
        db.commit()
        repository_id = repository.id

    provider = FixtureProvider(
        fixture,
        extra_metadata={
            "github_token": "secret-token",
            "Authorization": "Bearer secret-token",
        },
    )
    monkeypatch.setattr(
        "app.services.change_request.service.choose_change_request_provider",
        lambda url: provider,
    )
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    started = perf_counter()
    response = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={
            "url": fixture["url"],
            "use_vector": False,
            "use_graph": True,
        },
    )
    api_latency_ms = int((perf_counter() - started) * 1000)

    assert response.status_code == 201
    body = response.json()
    review = body["review"]
    tool_calls = review["tool_calls"]
    tool_names = [tool_call["tool_name"] for tool_call in tool_calls]

    assert body["change_request"]["platform"] == PLATFORM_GITHUB
    assert body["change_request"]["changed_file_count"] == 1
    assert review["status"] == TaskStatus.COMPLETED.value
    assert review["citations"]
    assert review["citations"][0]["file_path"] == fixture["changed_files"][0]
    assert review["citations"][0]["symbol_name"] == "ReviewPanel"
    assert "ReviewPanel" in review["impacted_symbols"]
    assert tool_names[:2] == ["analyze_diff", "code_search"]
    assert "get_symbol_context" in tool_names
    assert all(
        isinstance(tool_call["latency_ms"], int) and tool_call["latency_ms"] >= 0
        for tool_call in tool_calls
    )
    assert api_latency_ms >= 0
    assert any(trace["step_name"] == "ReviewReportWriter" for trace in review["traces"])
    assert review["markdown"] is not None
    assert "## Citations" in review["markdown"]

    with TestingSessionLocal() as db:
        stored_change_request = db.scalar(
            select(ChangeRequest).where(ChangeRequest.task_id == review["task_id"])
        )

    assert stored_change_request is not None
    safety_payload = json.dumps(body, ensure_ascii=False)
    assert stored_change_request.metadata_payload is not None
    safety_payload += stored_change_request.metadata_payload
    normalized_payload = safety_payload.lower()
    assert "secret-token" not in normalized_payload
    assert "authorization" not in normalized_payload
    assert "github_token" not in normalized_payload


class FixtureProvider:
    def __init__(
        self,
        fixture: dict[str, object],
        *,
        extra_metadata: dict[str, object] | None = None,
    ) -> None:
        self.fixture = fixture
        self.extra_metadata = extra_metadata or {}

    def parse_url(self, url: str) -> ChangeRequestRef:
        return parse_change_request_url(url)

    def fetch(self, ref: ChangeRequestRef, settings) -> FetchedChangeRequest:
        metadata = self.fixture["expected_metadata"]
        assert isinstance(metadata, dict)
        commit_titles = self.fixture["commit_titles"]
        assert isinstance(commit_titles, list)
        return FetchedChangeRequest(
            ref=ref,
            title=str(self.fixture["title"]),
            author=str(self.fixture["author"]),
            source_branch=str(self.fixture["source_branch"]),
            target_branch=str(self.fixture["target_branch"]),
            state=str(self.fixture["state"]),
            html_url=ref.url,
            diff_text=str(self.fixture["diff_text"]),
            files=[
                ChangeRequestFile(
                    path=str(path),
                    status="modified",
                    additions=int(metadata["addition_count"]),
                    deletions=int(metadata["deletion_count"]),
                    patch=None,
                )
                for path in self.fixture["changed_files"]
            ],
            commits=[
                ChangeRequestCommit(sha="demo-sha", title=str(title), author=str(self.fixture["author"]))
                for title in commit_titles
            ],
            metadata={
                "platform": PLATFORM_GITHUB,
                "api_source": "phase6_demo_fixture",
                **metadata,
                **self.extra_metadata,
            },
        )


def _override_get_db(TestingSessionLocal):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override_get_db


def _load_fixtures() -> list[dict[str, object]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _review_panel_chunk(repository_id: str, fixture: dict[str, object]) -> CodeChunk:
    file_path = str(fixture["changed_files"][0])
    source_path = REPO_ROOT / str(fixture["repository_path"]) / file_path
    content = source_path.read_text(encoding="utf-8")
    return CodeChunk(
        repository_id=repository_id,
        file_path=file_path,
        language=CodeLanguage.TYPESCRIPT.value,
        symbol_name="ReviewPanel",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=6,
        end_line=len(content.splitlines()),
        content_hash="phase6demo0000000000000000000000000000000000000000000000000000",
        content=content,
    )

from collections.abc import Generator
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import (
    ChangeRequest,
    Repository,
    RepositoryStatus,
    Task,
    TaskStatus,
    TaskType,
)
from app.services.change_request import (
    CHANGE_TYPE_MERGE_REQUEST,
    CHANGE_TYPE_PULL_REQUEST,
    PLATFORM_GITEE,
    PLATFORM_GITHUB,
    PLATFORM_GITLAB,
    PLATFORM_SELF_HOSTED_GITLAB,
    ChangeRequestAuthError,
    ChangeRequestCommit,
    ChangeRequestDiffTooLargeError,
    ChangeRequestFetchError,
    ChangeRequestFile,
    ChangeRequestRateLimitError,
    ChangeRequestRef,
)
from app.services.change_request.models import ChangeRequest as FetchedChangeRequest


def test_change_request_review_api_creates_review_and_persists_metadata(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value)

    provider = FakeProvider()
    monkeypatch.setattr(
        "app.services.change_request.service.choose_change_request_provider",
        lambda url: provider,
    )
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    app.dependency_overrides[get_settings] = lambda: Settings(github_token="secret-token")
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={
            "url": "https://github.com/openai/repolens/pull/42",
            "top_k": 8,
            "use_bm25": True,
            "use_vector": False,
            "use_graph": True,
            "run_static_check": False,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["change_request"]["repository_id"] == repository_id
    assert body["change_request"]["platform"] == PLATFORM_GITHUB
    assert body["change_request"]["change_type"] == CHANGE_TYPE_PULL_REQUEST
    assert body["change_request"]["owner"] == "openai"
    assert body["change_request"]["repo"] == "repolens"
    assert body["change_request"]["number"] == "42"
    assert body["change_request"]["title"] == "Improve review flow"
    assert body["change_request"]["changed_file_count"] == 1
    assert body["change_request"]["addition_count"] == 1
    assert body["change_request"]["deletion_count"] == 1
    assert "metadata" not in body["change_request"]
    assert "secret-token" not in response.text
    assert body["review"]["repository_id"] == repository_id
    assert body["review"]["status"] == TaskStatus.COMPLETED.value
    assert body["review"]["task_id"] == body["change_request"]["task_id"]
    assert [tool_call["tool_name"] for tool_call in body["review"]["tool_calls"]] == [
        "analyze_diff",
        "code_search",
    ]

    change_request_id = body["change_request"]["id"]
    task_id = body["review"]["task_id"]

    get_by_id = client.get(f"/api/change-requests/{change_request_id}")
    assert get_by_id.status_code == 200
    assert get_by_id.json()["id"] == change_request_id

    get_by_task = client.get(f"/api/change-requests/tasks/{task_id}")
    assert get_by_task.status_code == 200
    assert get_by_task.json()["id"] == change_request_id

    with TestingSessionLocal() as db:
        stored_change_request = db.get(ChangeRequest, change_request_id)
        stored_task = db.get(Task, task_id)

    assert stored_change_request is not None
    assert stored_change_request.task_id == task_id
    assert stored_change_request.repository_id == repository_id
    assert json.loads(stored_change_request.metadata_payload or "{}") == {
        "platform": "github",
        "api_source": "fake_provider",
        "changed_file_count": 1,
        "nested": {},
    }
    assert "secret-token" not in (stored_change_request.metadata_payload or "")
    assert "Authorization" not in (stored_change_request.metadata_payload or "")
    assert stored_task is not None
    assert stored_task.task_type == TaskType.REVIEW.value
    assert json.loads(stored_task.input_payload)["diff_text"].startswith("diff --git")
    assert provider.fetch_count == 1


def test_phase6_ext_change_request_review_api_closes_multi_platform_fetch_loop(
    monkeypatch,
) -> None:
    cases = [
        (
            PLATFORM_GITEE,
            CHANGE_TYPE_PULL_REQUEST,
            "https://gitee.com/team/demo/pulls/7",
            "https://gitee.com",
        ),
        (
            PLATFORM_GITLAB,
            CHANGE_TYPE_MERGE_REQUEST,
            "https://gitlab.com/team/demo/-/merge_requests/8",
            "https://gitlab.com",
        ),
        (
            PLATFORM_SELF_HOSTED_GITLAB,
            CHANGE_TYPE_MERGE_REQUEST,
            "https://git.example.com/team/demo/-/merge_requests/9",
            "https://git.example.com",
        ),
    ]

    for platform, change_type, url, base_url in cases:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=engine)

        with TestingSessionLocal() as db:
            repository_id = _insert_repository(db, RepositoryStatus.READY.value)

        provider = FakeProvider(
            platform=platform,
            change_type=change_type,
            url=url,
            base_url=base_url,
        )
        monkeypatch.setattr(
            "app.services.change_request.service.choose_change_request_provider",
            lambda request_url, provider=provider: provider,
        )
        app = create_app()
        app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
        client = TestClient(app)

        response = client.post(
            f"/api/repositories/{repository_id}/change-requests/reviews",
            json={"url": url, "use_vector": False},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["change_request"]["platform"] == platform
        assert body["change_request"]["change_type"] == change_type
        assert body["change_request"]["url"] == url
        assert body["change_request"]["changed_file_count"] == 1
        assert body["review"]["status"] == TaskStatus.COMPLETED.value
        assert body["review"]["task_id"] == body["change_request"]["task_id"]
        assert provider.fetch_count == 1

        with TestingSessionLocal() as db:
            stored_change_request = db.scalar(
                select(ChangeRequest).where(ChangeRequest.url == url)
            )

        assert stored_change_request is not None
        assert stored_change_request.platform == platform
        metadata = json.loads(stored_change_request.metadata_payload or "{}")
        assert metadata["platform"] == platform
        assert metadata["api_source"] == "phase6_ext_fake_provider"


def test_change_request_review_api_rejects_repository_before_ready(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.PARSING.value)

    provider = FakeProvider()
    monkeypatch.setattr(
        "app.services.change_request.service.choose_change_request_provider",
        lambda url: provider,
    )
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={"url": "https://github.com/openai/repolens/pull/42"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository must be ready before Review."
    assert provider.fetch_count == 0


def test_change_request_review_api_maps_provider_errors_and_missing_records() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    unsupported = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={"url": "https://bitbucket.org/openai/repolens/pull-requests/42"},
    )
    assert unsupported.status_code == 400
    assert "Unsupported PR/MR provider" in unsupported.json()["detail"]

    invalid = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={"url": "not-a-url"},
    )
    assert invalid.status_code == 422

    missing_by_id = client.get("/api/change-requests/missing")
    assert missing_by_id.status_code == 404
    assert missing_by_id.json()["detail"] == "Change request not found."

    missing_by_task = client.get("/api/change-requests/tasks/missing")
    assert missing_by_task.status_code == 404
    assert missing_by_task.json()["detail"] == "Change request not found."

    with TestingSessionLocal() as db:
        assert db.scalar(select(ChangeRequest)) is None
        assert db.scalar(select(Task)) is None


def test_change_request_review_api_enforces_service_diff_limit(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value)

    provider = FakeProvider(diff_text=_sample_diff() + ("x" * 20))
    monkeypatch.setattr(
        "app.services.change_request.service.choose_change_request_provider",
        lambda url: provider,
    )
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    app.dependency_overrides[get_settings] = lambda: Settings(change_request_max_diff_chars=10)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={"url": "https://github.com/openai/repolens/pull/42"},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "PR/MR diff exceeds REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS."
    with TestingSessionLocal() as db:
        assert db.scalar(select(ChangeRequest)) is None
        assert db.scalar(select(Task)) is None


def test_change_request_review_api_sanitizes_provider_error_details(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value)

    provider = ErrorProvider(
        ChangeRequestFetchError(
            "Platform failed with Authorization: Bearer secret-token and github_token=secret-token."
        )
    )
    monkeypatch.setattr(
        "app.services.change_request.service.choose_change_request_provider",
        lambda url: provider,
    )
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    app.dependency_overrides[get_settings] = lambda: Settings(github_token="secret-token")
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/change-requests/reviews",
        json={"url": "https://github.com/openai/repolens/pull/42"},
    )

    assert response.status_code == 502
    assert "secret-token" not in response.text
    assert "Authorization: Bearer [redacted]" in response.json()["detail"]
    assert "github_token=[redacted]" in response.json()["detail"]
    with TestingSessionLocal() as db:
        assert db.scalar(select(ChangeRequest)) is None
        assert db.scalar(select(Task)) is None


def test_change_request_review_api_maps_security_boundary_errors(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    cases = [
        (ChangeRequestAuthError("Platform authorization failed."), 400),
        (ChangeRequestRateLimitError("Platform rate limit exceeded."), 429),
        (
            ChangeRequestDiffTooLargeError(
                "PR/MR diff exceeds REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS."
            ),
            413,
        ),
        (ChangeRequestFetchError("Platform request failed."), 502),
    ]

    for exc, expected_status in cases:
        provider = ErrorProvider(exc)
        monkeypatch.setattr(
            "app.services.change_request.service.choose_change_request_provider",
            lambda url, provider=provider: provider,
        )

        response = client.post(
            f"/api/repositories/{repository_id}/change-requests/reviews",
            json={"url": "https://github.com/openai/repolens/pull/42"},
        )

        assert response.status_code == expected_status
        assert response.json()["detail"] == str(exc)

    with TestingSessionLocal() as db:
        assert db.scalar(select(ChangeRequest)) is None
        assert db.scalar(select(Task)) is None


class FakeProvider:
    def __init__(
        self,
        diff_text: str | None = None,
        *,
        platform: str = PLATFORM_GITHUB,
        change_type: str = CHANGE_TYPE_PULL_REQUEST,
        url: str = "https://github.com/openai/repolens/pull/42",
        base_url: str = "https://github.com",
    ) -> None:
        self.fetch_count = 0
        self.diff_text = diff_text or _sample_diff()
        self.platform = platform
        self.change_type = change_type
        self.url = url
        self.base_url = base_url

    def parse_url(self, url: str) -> ChangeRequestRef:
        return ChangeRequestRef(
            platform=self.platform,
            change_type=self.change_type,
            owner="team" if self.platform != PLATFORM_GITHUB else "openai",
            repo="demo" if self.platform != PLATFORM_GITHUB else "repolens",
            number="42",
            url=url,
            base_url=self.base_url,
        )

    def fetch(self, ref: ChangeRequestRef, settings: Settings) -> FetchedChangeRequest:
        self.fetch_count += 1
        return FetchedChangeRequest(
            ref=ref,
            title="Improve review flow",
            author="octocat",
            source_branch="feature/pr-review",
            target_branch="main",
            state="open",
            html_url=ref.url,
            diff_text=self.diff_text,
            files=[
                ChangeRequestFile(
                    path="app.py",
                    status="modified",
                    additions=1,
                    deletions=1,
                    patch="@@ -1 +1 @@",
                )
            ],
            commits=[ChangeRequestCommit(sha="abc123", title="Improve review flow", author="Ada")],
            metadata={
                "platform": ref.platform,
                "api_source": "phase6_ext_fake_provider"
                if ref.platform != PLATFORM_GITHUB
                else "fake_provider",
                "changed_file_count": 1,
                "github_token": settings.github_token,
                "nested": {"Authorization": "Bearer secret-token"},
            },
        )


class ErrorProvider(FakeProvider):
    def __init__(self, exc: Exception) -> None:
        super().__init__()
        self.exc = exc

    def fetch(self, ref: ChangeRequestRef, settings: Settings) -> FetchedChangeRequest:
        self.fetch_count += 1
        raise self.exc


def _insert_repository(db: Session, status: str) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=status,
    )
    db.add(repository)
    db.commit()
    return repository.id


def _sample_diff() -> str:
    return """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,1 +1,1 @@
-old()
+new()
"""


def _override_get_db(TestingSessionLocal):
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override_get_db

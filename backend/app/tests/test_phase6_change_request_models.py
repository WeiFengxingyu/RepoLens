import json

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    ChangeRequest,
    ChangeRequestPlatform,
    ChangeRequestType,
    Repository,
    RepositorySourceType,
    RepositoryStatus,
    Task,
    TaskStatus,
    TaskType,
)


def test_phase6_change_requests_table_is_created() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    indexes = {index["name"] for index in inspector.get_indexes("change_requests")}

    assert "change_requests" in tables
    assert "ix_change_requests_repository_ref" in indexes
    assert "ix_change_requests_task" in indexes
    assert "ix_change_requests_platform_created" in indexes


def test_change_request_round_trip_with_repository_and_task() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    safe_metadata = {
        "platform": "github",
        "api_source": "github_pulls",
        "changed_file_count": 2,
    }

    with Session(engine) as session:
        repository = Repository(
            name="demo",
            source_type=RepositorySourceType.GITHUB.value,
            source_url="https://github.com/example/demo",
            local_path="F:/Desktop/demo",
            status=RepositoryStatus.READY.value,
        )
        session.add(repository)
        session.flush()

        task = Task(
            repository_id=repository.id,
            task_type=TaskType.REVIEW.value,
            status=TaskStatus.COMPLETED.value,
            input_payload=json.dumps({"diff_text": "diff --git a/app.py b/app.py"}),
            output_payload=json.dumps({"summary": "ok"}),
        )
        session.add(task)
        session.flush()

        change_request = ChangeRequest(
            repository_id=repository.id,
            task_id=task.id,
            platform=ChangeRequestPlatform.GITHUB.value,
            change_type=ChangeRequestType.PULL_REQUEST.value,
            owner="example",
            repo="demo",
            number="123",
            url="https://github.com/example/demo/pull/123",
            title="Improve parser",
            author="octocat",
            source_branch="feature/parser",
            target_branch="main",
            state="open",
            changed_file_count=2,
            addition_count=10,
            deletion_count=3,
            commit_count=1,
            metadata_payload=json.dumps(safe_metadata),
        )
        session.add(change_request)
        session.commit()

        stored = session.get(ChangeRequest, change_request.id)

        assert stored is not None
        assert stored.repository.name == "demo"
        assert stored.task is not None
        assert stored.task.task_type == TaskType.REVIEW.value
        assert stored.platform == ChangeRequestPlatform.GITHUB.value
        assert stored.change_type == ChangeRequestType.PULL_REQUEST.value
        assert stored.source_branch == "feature/parser"
        assert stored.target_branch == "main"
        assert stored.changed_file_count == 2
        assert json.loads(stored.metadata_payload or "{}") == safe_metadata
        assert "github_token" not in (stored.metadata_payload or "")
        assert "Authorization" not in (stored.metadata_payload or "")
        assert repository.change_requests[0].id == stored.id
        assert task.change_requests[0].id == stored.id


def test_repository_delete_cascades_change_requests() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        repository = Repository(
            name="demo",
            source_type=RepositorySourceType.GITLAB.value,
            source_url="https://gitlab.com/example/demo",
            local_path="F:/Desktop/demo",
            status=RepositoryStatus.READY.value,
        )
        change_request = ChangeRequest(
            repository=repository,
            platform=ChangeRequestPlatform.GITLAB.value,
            change_type=ChangeRequestType.MERGE_REQUEST.value,
            owner="example",
            repo="demo",
            number="7",
            url="https://gitlab.com/example/demo/-/merge_requests/7",
            title="Refine workbench",
        )
        session.add(repository)
        session.flush()
        change_request_id = change_request.id

        session.delete(repository)
        session.commit()

        assert session.scalar(select(ChangeRequest).where(ChangeRequest.id == change_request_id)) is None

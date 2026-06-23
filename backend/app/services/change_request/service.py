import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import ChangeRequest as ChangeRequestRecord
from app.schemas.change_request import (
    ChangeRequestMetadataResponse,
    ChangeRequestReviewCreateRequest,
    ChangeRequestReviewResponse,
)
from app.schemas.review import ReviewCreateRequest
from app.services.change_request.models import ChangeRequest as FetchedChangeRequest
from app.services.change_request.providers import (
    ChangeRequestDiffTooLargeError,
    choose_change_request_provider,
)
from app.services.review import ReviewService


class ChangeRequestReviewService:
    def __init__(self, db: Session):
        self.db = db

    def create_review_from_url(
        self,
        repository_id: str,
        request: ChangeRequestReviewCreateRequest,
        settings: Settings,
    ) -> ChangeRequestReviewResponse:
        review_service = ReviewService(self.db)
        repository = review_service.get_repository(repository_id)
        if repository is None:
            raise ChangeRequestRepositoryNotFoundError("Repository not found.")
        review_service.ensure_repository_ready(repository)

        provider = choose_change_request_provider(request.url)
        ref = provider.parse_url(request.url)
        fetched = provider.fetch(ref, settings)
        _ensure_diff_within_limit(fetched.diff_text, settings)
        record = self._create_change_request_record(repository_id, fetched)

        review_request = ReviewCreateRequest(
            diff_text=fetched.diff_text,
            top_k=request.top_k,
            use_bm25=request.use_bm25,
            use_vector=request.use_vector,
            use_graph=request.use_graph,
            run_static_check=request.run_static_check,
        )
        task = review_service.create_review_task(repository, review_request)
        record.task_id = task.id
        self.db.commit()
        self.db.refresh(record)

        task = review_service.run_review_task(task, review_request, settings)
        return ChangeRequestReviewResponse(
            change_request=self.build_metadata_response(record),
            review=review_service.build_task_response(task),
        )

    def get_change_request(self, change_request_id: str) -> ChangeRequestRecord | None:
        return self.db.get(ChangeRequestRecord, change_request_id)

    def get_change_request_by_task(self, task_id: str) -> ChangeRequestRecord | None:
        return self.db.scalar(
            select(ChangeRequestRecord).where(ChangeRequestRecord.task_id == task_id)
        )

    def build_metadata_response(
        self,
        change_request: ChangeRequestRecord,
    ) -> ChangeRequestMetadataResponse:
        return ChangeRequestMetadataResponse(
            id=change_request.id,
            repository_id=change_request.repository_id,
            task_id=change_request.task_id,
            platform=change_request.platform,
            change_type=change_request.change_type,
            owner=change_request.owner,
            repo=change_request.repo,
            number=change_request.number,
            url=change_request.url,
            title=change_request.title,
            author=change_request.author,
            source_branch=change_request.source_branch,
            target_branch=change_request.target_branch,
            state=change_request.state,
            changed_file_count=change_request.changed_file_count,
            addition_count=change_request.addition_count,
            deletion_count=change_request.deletion_count,
            commit_count=change_request.commit_count,
            created_at=change_request.created_at,
            updated_at=change_request.updated_at,
        )

    def _create_change_request_record(
        self,
        repository_id: str,
        fetched: FetchedChangeRequest,
    ) -> ChangeRequestRecord:
        record = ChangeRequestRecord(
            repository_id=repository_id,
            platform=fetched.ref.platform,
            change_type=fetched.ref.change_type,
            owner=fetched.ref.owner,
            repo=fetched.ref.repo,
            number=fetched.ref.number,
            url=fetched.ref.url,
            title=fetched.title,
            author=fetched.author or None,
            source_branch=fetched.source_branch,
            target_branch=fetched.target_branch,
            state=fetched.state,
            changed_file_count=len(fetched.files),
            addition_count=sum(file.additions for file in fetched.files),
            deletion_count=sum(file.deletions for file in fetched.files),
            commit_count=len(fetched.commits),
            metadata_payload=json.dumps(_safe_metadata(fetched.metadata), ensure_ascii=False),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record


class ChangeRequestRepositoryNotFoundError(ValueError):
    pass


def _ensure_diff_within_limit(diff_text: str, settings: Settings) -> None:
    if len(diff_text) > settings.change_request_max_diff_chars:
        raise ChangeRequestDiffTooLargeError(
            "PR/MR diff exceeds REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS."
        )


def _safe_metadata(metadata: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in metadata.items():
        normalized_key = key.lower()
        if "token" in normalized_key or "authorization" in normalized_key:
            continue
        safe[key] = _safe_metadata_value(value)
    return safe


def _safe_metadata_value(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_safe_metadata_value(item) for item in value]
    if isinstance(value, dict):
        return _safe_metadata({str(key): item for key, item in value.items()})
    return str(value)

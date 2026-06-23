import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas import (
    ChangeRequestMetadataResponse,
    ChangeRequestReviewCreateRequest,
    ChangeRequestReviewResponse,
)
from app.services.change_request import (
    ChangeRequestAuthError,
    ChangeRequestDiffTooLargeError,
    ChangeRequestFetchError,
    ChangeRequestNotFoundError,
    ChangeRequestProviderNotImplementedError,
    ChangeRequestRateLimitError,
    ChangeRequestValidationError,
    UnsupportedChangeRequestProviderError,
)
from app.services.change_request.service import (
    ChangeRequestRepositoryNotFoundError,
    ChangeRequestReviewService,
)
from app.services.review import ReviewRepositoryNotReadyError, ReviewValidationError

router = APIRouter(tags=["change-requests"])


@router.post(
    "/api/repositories/{repository_id}/change-requests/reviews",
    response_model=ChangeRequestReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_change_request_review(
    repository_id: str,
    request: ChangeRequestReviewCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    service = ChangeRequestReviewService(db)
    try:
        return service.create_review_from_url(repository_id, request, settings)
    except ChangeRequestRepositoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ReviewRepositoryNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ChangeRequestValidationError as exc:
        raise HTTPException(status_code=422, detail=_safe_error_detail(exc, settings)) from exc
    except UnsupportedChangeRequestProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ChangeRequestProviderNotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ChangeRequestAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ChangeRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ChangeRequestRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ChangeRequestDiffTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except ChangeRequestFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_safe_error_detail(exc, settings),
        ) from exc
    except (ReviewValidationError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=_safe_error_detail(exc, settings)) from exc


@router.get(
    "/api/change-requests/tasks/{task_id}",
    response_model=ChangeRequestMetadataResponse,
)
def get_change_request_by_task(task_id: str, db: Session = Depends(get_db)):
    service = ChangeRequestReviewService(db)
    change_request = service.get_change_request_by_task(task_id)
    if change_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found.",
        )
    return service.build_metadata_response(change_request)


@router.get(
    "/api/change-requests/{change_request_id}",
    response_model=ChangeRequestMetadataResponse,
)
def get_change_request(change_request_id: str, db: Session = Depends(get_db)):
    service = ChangeRequestReviewService(db)
    change_request = service.get_change_request(change_request_id)
    if change_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found.",
        )
    return service.build_metadata_response(change_request)


def _safe_error_detail(exc: Exception, settings: Settings) -> str:
    detail = str(exc)
    for secret in (settings.github_token, settings.gitee_token, settings.gitlab_token):
        if secret:
            detail = detail.replace(secret, "[redacted]")
    detail = re.sub(
        r"(?i)authorization\s*[:=]\s*bearer\s+[^\s,;]+",
        "Authorization: Bearer [redacted]",
        detail,
    )
    detail = re.sub(r"(?i)bearer\s+[^\s,;]+", "Bearer [redacted]", detail)
    return detail

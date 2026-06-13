from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import TaskType
from app.schemas import ReviewCreateRequest, ReviewTaskResponse
from app.services.review import (
    ReviewRepositoryNotReadyError,
    ReviewService,
    ReviewValidationError,
)

router = APIRouter(tags=["reviews"])


@router.post(
    "/api/repositories/{repository_id}/reviews",
    response_model=ReviewTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    repository_id: str,
    request: ReviewCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    service = ReviewService(db)
    repository = service.get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    try:
        service.ensure_repository_ready(repository)
        task = service.create_review_task(repository, request)
        task = service.run_review_task(task, request, settings)
    except ReviewRepositoryNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ReviewValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return service.build_task_response(task)


@router.get("/api/reviews/{task_id}", response_model=ReviewTaskResponse)
def get_review(task_id: str, db: Session = Depends(get_db)):
    service = ReviewService(db)
    task = service.get_task(task_id)
    if task is None or task.task_type != TaskType.REVIEW.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review task not found.")
    return service.build_task_response(task)

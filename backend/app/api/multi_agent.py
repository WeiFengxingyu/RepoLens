from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import TaskType
from app.schemas import MultiAgentReviewCreateRequest, MultiAgentReviewResponse
from app.services.multi_agent import (
    MultiAgentReviewRepositoryNotReadyError,
    MultiAgentReviewService,
    MultiAgentReviewValidationError,
)

router = APIRouter(tags=["multi-agent"])


@router.post(
    "/api/repositories/{repository_id}/multi-agent-reviews",
    response_model=MultiAgentReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_multi_agent_review(
    repository_id: str,
    request: MultiAgentReviewCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    service = MultiAgentReviewService(db)
    repository = service.get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    try:
        service.ensure_repository_ready(repository)
        task = service.create_review_task(repository, request)
        task = service.run_review_task(task, request, settings)
    except MultiAgentReviewRepositoryNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except MultiAgentReviewValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return service.build_task_response(task)


@router.get("/api/multi-agent-reviews/{task_id}", response_model=MultiAgentReviewResponse)
def get_multi_agent_review(task_id: str, db: Session = Depends(get_db)):
    service = MultiAgentReviewService(db)
    task = service.get_task(task_id)
    if task is None or task.task_type != TaskType.MULTI_AGENT_REVIEW.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Multi-Agent Review task not found.",
        )
    return service.build_task_response(task)


@router.get("/api/agent-sessions/{session_id}", response_model=MultiAgentReviewResponse)
def get_agent_session(session_id: str, db: Session = Depends(get_db)):
    service = MultiAgentReviewService(db)
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found.",
        )
    return service.build_session_response(session)

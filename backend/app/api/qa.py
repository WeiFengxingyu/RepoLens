from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas import QACreateRequest, QATaskResponse
from app.services.qa import QAService
from app.services.qa.service import RepositoryNotReadyError

router = APIRouter(tags=["qa"])


@router.post(
    "/api/repositories/{repository_id}/questions",
    response_model=QATaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    repository_id: str,
    request: QACreateRequest,
    db: Session = Depends(get_db),
):
    service = QAService(db)
    repository = service.get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    try:
        service.ensure_repository_ready(repository)
    except RepositoryNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    task = service.create_question_task(repository, request)
    task = service.run_question_task(task, request, get_settings())
    return service.build_task_response(task)


@router.get("/api/tasks/{task_id}", response_model=QATaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    service = QAService(db)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return service.build_task_response(task)

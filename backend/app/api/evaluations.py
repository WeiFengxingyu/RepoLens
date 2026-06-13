from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas import EvaluationCreateRequest, EvaluationRunResponse, EvaluationRunSummary
from app.services.evaluation import (
    EvaluationRepositoryNotReadyError,
    EvaluationService,
    EvaluationValidationError,
)

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


@router.post("", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    request: EvaluationCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    service = EvaluationService(db)
    try:
        return service.create_and_run(request, settings)
    except EvaluationRepositoryNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EvaluationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[EvaluationRunSummary])
def list_evaluations(db: Session = Depends(get_db)):
    return EvaluationService(db).list_runs()


@router.get("/{run_id}", response_model=EvaluationRunResponse)
def get_evaluation(run_id: str, db: Session = Depends(get_db)):
    service = EvaluationService(db)
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found.")
    return service.build_run_response(run)

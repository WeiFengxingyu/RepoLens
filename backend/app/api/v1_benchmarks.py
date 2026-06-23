from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas import V1BenchmarkCreateRequest, V1BenchmarkResponse
from app.services.v1_benchmark.service import (
    V1BenchmarkRepositoryNotReadyError,
    V1BenchmarkService,
    V1BenchmarkValidationError,
)

router = APIRouter(prefix="/api/v1-benchmarks", tags=["v1-benchmarks"])


@router.post("", response_model=V1BenchmarkResponse, status_code=status.HTTP_201_CREATED)
def create_v1_benchmark(
    request: V1BenchmarkCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    service = V1BenchmarkService(db)
    try:
        return service.create_and_run(request, settings)
    except V1BenchmarkRepositoryNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except V1BenchmarkValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

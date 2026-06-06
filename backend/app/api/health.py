from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/api/status")
def status() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "phase": "phase0",
        "environment": settings.environment,
        "components": {
            "api": "ready",
            "database": "configured",
            "qdrant": "configured",
            "agent": "planned",
        },
    }


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.change_requests import router as change_requests_router
from app.api.evaluations import router as evaluations_router
from app.api.health import router as health_router
from app.api.mcp import router as mcp_router
from app.api.multi_agent import router as multi_agent_router
from app.api.qa import router as qa_router
from app.api.repositories import router as repositories_router
from app.api.reviews import router as reviews_router
from app.api.v1_benchmarks import router as v1_benchmarks_router
from app.core.config import get_settings
from app.db.init_db import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_db()
    app.include_router(health_router)
    app.include_router(repositories_router)
    app.include_router(qa_router)
    app.include_router(reviews_router)
    app.include_router(change_requests_router)
    app.include_router(evaluations_router)
    app.include_router(mcp_router)
    app.include_router(multi_agent_router)
    app.include_router(v1_benchmarks_router)
    return app


app = create_app()

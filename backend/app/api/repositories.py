from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas import (
    EvidenceResponse,
    RepositoryDetail,
    RepositoryImportRequest,
    RepositoryStatusResponse,
    RepositorySummary,
    RetrievalDebugInfo,
    RetrievalDebugRequest,
    RetrievalDebugResponse,
    VectorIndexResponse,
)
from app.services.indexing import (
    EmbeddingDisabledError,
    EmbeddingRequestError,
    OpenAICompatibleEmbeddingAdapter,
    QdrantStoreError,
    QdrantVectorStore,
    embedding_config_from_settings,
    index_repository_chunks,
    qdrant_config_from_settings,
)
from app.services.repository import ProviderError, RepositoryService
from app.services.retrieval import retrieve_repository

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.post("", response_model=RepositoryDetail, status_code=status.HTTP_201_CREATED)
def import_repository(request: RepositoryImportRequest, db: Session = Depends(get_db)):
    service = RepositoryService(db)
    try:
        return service.import_repository(request)
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[RepositorySummary])
def list_repositories(db: Session = Depends(get_db)):
    return RepositoryService(db).list_repositories()


@router.get("/{repository_id}", response_model=RepositoryDetail)
def get_repository(repository_id: str, db: Session = Depends(get_db)):
    repository = RepositoryService(db).get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    return repository


@router.get("/{repository_id}/status", response_model=RepositoryStatusResponse)
def get_repository_status(repository_id: str, db: Session = Depends(get_db)):
    repository_status = RepositoryService(db).get_status(repository_id)
    if repository_status is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    return repository_status


@router.post("/{repository_id}/retrieve", response_model=RetrievalDebugResponse)
def retrieve_repository_evidences(
    repository_id: str,
    request: RetrievalDebugRequest,
    db: Session = Depends(get_db),
):
    repository = RepositoryService(db).get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    if repository.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository must be ready before retrieval.",
        )

    result = retrieve_repository(
        db,
        repository_id,
        request.query,
        get_settings(),
        top_k=request.top_k,
        use_bm25=request.use_bm25,
        use_vector=request.use_vector,
        use_graph=request.use_graph,
    )
    return RetrievalDebugResponse(
        repository_id=result.repository_id,
        query=result.query,
        evidences=[
            EvidenceResponse(
                evidence_id=evidence.evidence_id,
                chunk_id=evidence.chunk_id,
                repository_id=evidence.repository_id,
                file_path=evidence.file_path,
                start_line=evidence.start_line,
                end_line=evidence.end_line,
                symbol_name=evidence.symbol_name,
                symbol_type=evidence.symbol_type,
                language=evidence.language,
                source=evidence.source,
                sources=evidence.sources,
                score=evidence.score,
                bm25_score=evidence.bm25_score,
                vector_score=evidence.vector_score,
                graph_score=evidence.graph_score,
                snippet=evidence.snippet,
                metadata=evidence.metadata,
            )
            for evidence in result.evidences
        ],
        debug=RetrievalDebugInfo(
            bm25_count=result.debug.bm25_count,
            vector_count=result.debug.vector_count,
            graph_count=result.debug.graph_count,
            merged_count=result.debug.merged_count,
            evidence_count=result.debug.evidence_count,
            vector_disabled_reason=result.debug.vector_disabled_reason,
            context_truncated=result.debug.context_truncated,
        ),
    )


@router.post("/{repository_id}/indexes/vector", response_model=VectorIndexResponse)
def index_repository_vectors(repository_id: str, db: Session = Depends(get_db)):
    repository = RepositoryService(db).get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")

    settings = get_settings()
    embedding_adapter = OpenAICompatibleEmbeddingAdapter(embedding_config_from_settings(settings))
    vector_store = QdrantVectorStore(qdrant_config_from_settings(settings))
    try:
        result = index_repository_chunks(
            db,
            repository_id,
            embedding_adapter=embedding_adapter,
            vector_store=vector_store,
        )
    except EmbeddingDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmbeddingRequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except QdrantStoreError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return VectorIndexResponse(
        repository_id=result.repository_id,
        status="completed",
        collection_name=result.collection_name,
        chunk_count=result.chunk_count,
        vector_count=result.vector_count,
        dimension=result.dimension,
    )

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.review import ReviewTaskResponse


class ChangeRequestReviewCreateRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=8, ge=1, le=50)
    use_bm25: bool = True
    use_vector: bool = True
    use_graph: bool = True
    run_static_check: bool = False


class ChangeRequestMetadataResponse(BaseModel):
    id: str
    repository_id: str
    task_id: str | None
    platform: str
    change_type: str
    owner: str
    repo: str
    number: str
    url: str
    title: str
    author: str | None
    source_branch: str | None
    target_branch: str | None
    state: str | None
    changed_file_count: int
    addition_count: int
    deletion_count: int
    commit_count: int
    created_at: datetime
    updated_at: datetime


class ChangeRequestReviewResponse(BaseModel):
    change_request: ChangeRequestMetadataResponse
    review: ReviewTaskResponse

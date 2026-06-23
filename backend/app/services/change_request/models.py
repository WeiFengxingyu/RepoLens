from dataclasses import dataclass

PLATFORM_GITHUB = "github"
PLATFORM_GITEE = "gitee"
PLATFORM_GITLAB = "gitlab"
PLATFORM_SELF_HOSTED_GITLAB = "self_hosted_gitlab"

CHANGE_TYPE_PULL_REQUEST = "pull_request"
CHANGE_TYPE_MERGE_REQUEST = "merge_request"


@dataclass(frozen=True)
class ChangeRequestRef:
    platform: str
    change_type: str
    owner: str
    repo: str
    number: str
    url: str
    base_url: str | None = None


@dataclass(frozen=True)
class ChangeRequestFile:
    path: str
    status: str
    additions: int
    deletions: int
    patch: str | None = None


@dataclass(frozen=True)
class ChangeRequestCommit:
    sha: str
    title: str
    author: str | None = None


@dataclass(frozen=True)
class ChangeRequest:
    ref: ChangeRequestRef
    title: str
    author: str
    source_branch: str | None
    target_branch: str | None
    state: str | None
    html_url: str
    diff_text: str
    files: list[ChangeRequestFile]
    commits: list[ChangeRequestCommit]
    metadata: dict[str, object]

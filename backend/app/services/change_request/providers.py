from __future__ import annotations

from abc import ABC, abstractmethod
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

from app.core.config import Settings
from app.services.change_request.models import (
    CHANGE_TYPE_MERGE_REQUEST,
    CHANGE_TYPE_PULL_REQUEST,
    PLATFORM_GITEE,
    PLATFORM_GITHUB,
    PLATFORM_GITLAB,
    PLATFORM_SELF_HOSTED_GITLAB,
    ChangeRequest,
    ChangeRequestCommit,
    ChangeRequestFile,
    ChangeRequestRef,
)


class ChangeRequestValidationError(ValueError):
    pass


class UnsupportedChangeRequestProviderError(ValueError):
    pass


class ChangeRequestProviderNotImplementedError(NotImplementedError):
    pass


class ChangeRequestFetchError(RuntimeError):
    pass


class ChangeRequestAuthError(ChangeRequestFetchError):
    pass


class ChangeRequestNotFoundError(ChangeRequestFetchError):
    pass


class ChangeRequestRateLimitError(ChangeRequestFetchError):
    pass


class ChangeRequestDiffTooLargeError(ChangeRequestFetchError):
    pass


@dataclass(frozen=True)
class HTTPResponse:
    status_code: int
    body: str
    headers: dict[str, str]


@dataclass(frozen=True)
class _DiffFile:
    file: ChangeRequestFile
    old_path: str
    new_path: str


class HTTPTransport:
    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        timeout: float,
    ) -> HTTPResponse:
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                return HTTPResponse(
                    status_code=response.status,
                    body=body,
                    headers={key.lower(): value for key, value in response.headers.items()},
                )
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return HTTPResponse(
                status_code=exc.code,
                body=body,
                headers={key.lower(): value for key, value in exc.headers.items()},
            )
        except URLError as exc:
            raise ChangeRequestFetchError("Platform request failed.") from exc


class ChangeRequestProvider(ABC):
    platform: str

    @abstractmethod
    def detect(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse_url(self, url: str) -> ChangeRequestRef:
        raise NotImplementedError

    def fetch(self, ref: ChangeRequestRef, settings: Settings) -> ChangeRequest:
        raise ChangeRequestProviderNotImplementedError(
            f"{self.platform} change request client is not implemented."
        )


class GitHubChangeRequestProvider(ChangeRequestProvider):
    platform = PLATFORM_GITHUB

    def __init__(self, transport: HTTPTransport | None = None) -> None:
        self.transport = transport or HTTPTransport()

    def detect(self, url: str) -> bool:
        parsed = _parse_http_url(url)
        return parsed.netloc.lower() == "github.com" and "/pull/" in parsed.path

    def parse_url(self, url: str) -> ChangeRequestRef:
        parsed = _parse_http_url(url)
        parts = _path_parts(parsed.path)
        if len(parts) != 4 or parts[2] != "pull":
            raise ChangeRequestValidationError(
                "GitHub PR URL must match https://github.com/{owner}/{repo}/pull/{number}."
            )
        owner, repo, _, number = parts
        _validate_number(number)
        return ChangeRequestRef(
            platform=PLATFORM_GITHUB,
            change_type=CHANGE_TYPE_PULL_REQUEST,
            owner=owner,
            repo=repo,
            number=number,
            url=_canonical_url(parsed),
            base_url="https://github.com",
        )

    def fetch(self, ref: ChangeRequestRef, settings: Settings) -> ChangeRequest:
        if ref.platform != PLATFORM_GITHUB:
            raise ChangeRequestValidationError("GitHub provider can only fetch GitHub refs.")

        base_url = settings.github_base_url.rstrip("/")
        api_path = f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
        headers = _github_headers(settings.github_token)
        timeout = settings.change_request_timeout_seconds

        metadata = _json_request(
            self.transport,
            f"{base_url}{api_path}",
            headers=headers,
            timeout=timeout,
        )
        files_payload = _json_request(
            self.transport,
            f"{base_url}{api_path}/files",
            headers=headers,
            timeout=timeout,
        )
        commits_payload = _json_request(
            self.transport,
            f"{base_url}{api_path}/commits",
            headers=headers,
            timeout=timeout,
        )
        diff_text = _text_request(
            self.transport,
            f"{base_url}{api_path}",
            headers={**headers, "Accept": "application/vnd.github.v3.diff"},
            timeout=timeout,
        )
        if len(diff_text) > settings.change_request_max_diff_chars:
            raise ChangeRequestDiffTooLargeError(
                "PR/MR diff exceeds REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS."
            )

        files = _github_files(files_payload)
        commits = _github_commits(commits_payload)
        user = metadata.get("user") if isinstance(metadata, dict) else {}
        head = metadata.get("head") if isinstance(metadata, dict) else {}
        base = metadata.get("base") if isinstance(metadata, dict) else {}

        return ChangeRequest(
            ref=ref,
            title=_str_or_empty(metadata.get("title")),
            author=_str_or_empty(user.get("login") if isinstance(user, dict) else ""),
            source_branch=_optional_str(head.get("ref") if isinstance(head, dict) else None),
            target_branch=_optional_str(base.get("ref") if isinstance(base, dict) else None),
            state=_optional_str(metadata.get("state")),
            html_url=_str_or_empty(metadata.get("html_url")) or ref.url,
            diff_text=diff_text,
            files=files,
            commits=commits,
            metadata={
                "platform": PLATFORM_GITHUB,
                "api_source": "github_pulls",
                "changed_file_count": len(files),
                "addition_count": sum(file.additions for file in files),
                "deletion_count": sum(file.deletions for file in files),
                "commit_count": len(commits),
            },
        )


class GiteeChangeRequestProvider(ChangeRequestProvider):
    platform = PLATFORM_GITEE

    def __init__(self, transport: HTTPTransport | None = None) -> None:
        self.transport = transport or HTTPTransport()

    def detect(self, url: str) -> bool:
        parsed = _parse_http_url(url)
        return parsed.netloc.lower() == "gitee.com" and "/pulls/" in parsed.path

    def parse_url(self, url: str) -> ChangeRequestRef:
        parsed = _parse_http_url(url)
        parts = _path_parts(parsed.path)
        if len(parts) != 4 or parts[2] != "pulls":
            raise ChangeRequestValidationError(
                "Gitee PR URL must match https://gitee.com/{owner}/{repo}/pulls/{number}."
            )
        owner, repo, _, number = parts
        _validate_number(number)
        return ChangeRequestRef(
            platform=PLATFORM_GITEE,
            change_type=CHANGE_TYPE_PULL_REQUEST,
            owner=owner,
            repo=repo,
            number=number,
            url=_canonical_url(parsed),
            base_url="https://gitee.com",
        )

    def fetch(self, ref: ChangeRequestRef, settings: Settings) -> ChangeRequest:
        if ref.platform != PLATFORM_GITEE:
            raise ChangeRequestValidationError("Gitee provider can only fetch Gitee refs.")

        base_url = settings.gitee_base_url.rstrip("/")
        api_path = f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
        headers = _gitee_headers()
        timeout = settings.change_request_timeout_seconds

        metadata = _json_request(
            self.transport,
            _gitee_url(f"{base_url}{api_path}", settings.gitee_token),
            headers=headers,
            timeout=timeout,
        )
        files_payload = _json_request(
            self.transport,
            _gitee_url(f"{base_url}{api_path}/files", settings.gitee_token),
            headers=headers,
            timeout=timeout,
        )
        commits_payload = _json_request(
            self.transport,
            _gitee_url(f"{base_url}{api_path}/commits", settings.gitee_token),
            headers=headers,
            timeout=timeout,
        )

        if not isinstance(metadata, dict):
            raise ChangeRequestFetchError("Gitee pull request response must be an object.")
        diff_files = _gitee_diff_files(files_payload)
        files = [item.file for item in diff_files]
        commits = _gitee_commits(commits_payload)
        diff_text = _build_diff_text(diff_files)
        if len(diff_text) > settings.change_request_max_diff_chars:
            raise ChangeRequestDiffTooLargeError(
                "PR/MR diff exceeds REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS."
            )

        return ChangeRequest(
            ref=ref,
            title=_str_or_empty(metadata.get("title")),
            author=_author_from_payload(metadata),
            source_branch=_first_present_str(
                _nested_str(metadata, "head", "ref"),
                metadata.get("head_branch"),
                metadata.get("source_branch"),
            ),
            target_branch=_first_present_str(
                _nested_str(metadata, "base", "ref"),
                metadata.get("base_branch"),
                metadata.get("target_branch"),
            ),
            state=_optional_str(metadata.get("state")),
            html_url=_str_or_empty(metadata.get("html_url")) or ref.url,
            diff_text=diff_text,
            files=files,
            commits=commits,
            metadata={
                "platform": PLATFORM_GITEE,
                "api_source": "gitee_pulls",
                "changed_file_count": len(files),
                "addition_count": sum(file.additions for file in files),
                "deletion_count": sum(file.deletions for file in files),
                "commit_count": len(commits),
            },
        )


class GitLabChangeRequestProvider(ChangeRequestProvider):
    platform = PLATFORM_GITLAB

    def __init__(self, transport: HTTPTransport | None = None) -> None:
        self.transport = transport or HTTPTransport()

    def detect(self, url: str) -> bool:
        parsed = _parse_http_url(url)
        return "/-/merge_requests/" in parsed.path

    def parse_url(self, url: str) -> ChangeRequestRef:
        parsed = _parse_http_url(url)
        parts = _path_parts(parsed.path)
        try:
            marker_index = parts.index("-")
        except ValueError as exc:
            raise ChangeRequestValidationError(
                "GitLab MR URL must contain /-/merge_requests/{number}."
            ) from exc

        if len(parts) != marker_index + 3 or parts[marker_index + 1] != "merge_requests":
            raise ChangeRequestValidationError(
                "GitLab MR URL must match https://host/{namespace}/{repo}/-/merge_requests/{number}."
            )
        namespace_parts = parts[:marker_index]
        if len(namespace_parts) < 2:
            raise ChangeRequestValidationError("GitLab MR URL must include namespace and repo.")
        number = parts[marker_index + 2]
        _validate_number(number)
        platform = (
            PLATFORM_GITLAB
            if parsed.netloc.lower() == "gitlab.com"
            else PLATFORM_SELF_HOSTED_GITLAB
        )
        return ChangeRequestRef(
            platform=platform,
            change_type=CHANGE_TYPE_MERGE_REQUEST,
            owner="/".join(namespace_parts[:-1]),
            repo=namespace_parts[-1],
            number=number,
            url=_canonical_url(parsed),
            base_url=f"{parsed.scheme}://{parsed.netloc}",
        )

    def fetch(self, ref: ChangeRequestRef, settings: Settings) -> ChangeRequest:
        if ref.platform not in {PLATFORM_GITLAB, PLATFORM_SELF_HOSTED_GITLAB}:
            raise ChangeRequestValidationError("GitLab provider can only fetch GitLab refs.")

        base_url = _gitlab_api_base_url(ref, settings)
        project_id = quote(f"{ref.owner}/{ref.repo}", safe="")
        api_path = f"/projects/{project_id}/merge_requests/{ref.number}"
        headers = _gitlab_headers(settings.gitlab_token)
        timeout = settings.change_request_timeout_seconds

        metadata = _json_request(
            self.transport,
            f"{base_url}{api_path}",
            headers=headers,
            timeout=timeout,
        )
        diffs_payload = _json_request(
            self.transport,
            f"{base_url}{api_path}/diffs",
            headers=headers,
            timeout=timeout,
        )
        commits_payload = _json_request(
            self.transport,
            f"{base_url}{api_path}/commits",
            headers=headers,
            timeout=timeout,
        )

        if not isinstance(metadata, dict):
            raise ChangeRequestFetchError("GitLab merge request response must be an object.")
        diff_files = _gitlab_diff_files(diffs_payload)
        files = [item.file for item in diff_files]
        commits = _gitlab_commits(commits_payload)
        diff_text = _build_diff_text(diff_files)
        if len(diff_text) > settings.change_request_max_diff_chars:
            raise ChangeRequestDiffTooLargeError(
                "PR/MR diff exceeds REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS."
            )

        return ChangeRequest(
            ref=ref,
            title=_str_or_empty(metadata.get("title")),
            author=_author_from_payload(metadata),
            source_branch=_optional_str(metadata.get("source_branch")),
            target_branch=_optional_str(metadata.get("target_branch")),
            state=_optional_str(metadata.get("state")),
            html_url=_str_or_empty(metadata.get("web_url")) or ref.url,
            diff_text=diff_text,
            files=files,
            commits=commits,
            metadata={
                "platform": ref.platform,
                "api_source": "gitlab_merge_requests",
                "changed_file_count": len(files),
                "addition_count": sum(file.additions for file in files),
                "deletion_count": sum(file.deletions for file in files),
                "commit_count": len(commits),
            },
        )


def choose_change_request_provider(url: str) -> ChangeRequestProvider:
    providers: list[ChangeRequestProvider] = [
        GitHubChangeRequestProvider(),
        GiteeChangeRequestProvider(),
        GitLabChangeRequestProvider(),
    ]
    for provider in providers:
        if provider.detect(url):
            return provider
    raise UnsupportedChangeRequestProviderError(
        "Unsupported PR/MR provider. Supported URL formats include GitHub pull requests, "
        "Gitee pull requests, and GitLab merge requests."
    )


def parse_change_request_url(url: str) -> ChangeRequestRef:
    provider = choose_change_request_provider(url)
    return provider.parse_url(url)


def _github_headers(token: str) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoLens",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _gitee_headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "User-Agent": "RepoLens",
    }


def _gitlab_headers(token: str) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "RepoLens",
    }
    if token:
        headers["PRIVATE-TOKEN"] = token
    return headers


def _gitee_url(url: str, token: str) -> str:
    if not token:
        return url
    parsed = urlparse(url)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("access_token", token))
    return urlunparse(parsed._replace(query=urlencode(query)))


def _gitlab_api_base_url(ref: ChangeRequestRef, settings: Settings) -> str:
    configured = settings.gitlab_base_url.rstrip("/")
    if ref.platform == PLATFORM_SELF_HOSTED_GITLAB and configured == "https://gitlab.com/api/v4":
        if not ref.base_url:
            raise ChangeRequestValidationError("Self-hosted GitLab MR URL is missing base URL.")
        return f"{ref.base_url.rstrip('/')}/api/v4"
    return configured


def _json_request(
    transport: HTTPTransport,
    url: str,
    *,
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any] | list[Any]:
    response = transport.get(url, headers=headers, timeout=timeout)
    _raise_for_status(response)
    try:
        payload = json.loads(response.body)
    except json.JSONDecodeError as exc:
        raise ChangeRequestFetchError("Platform response was not valid JSON.") from exc
    if not isinstance(payload, (dict, list)):
        raise ChangeRequestFetchError("Platform JSON response must be an object or array.")
    return payload


def _text_request(
    transport: HTTPTransport,
    url: str,
    *,
    headers: dict[str, str],
    timeout: float,
) -> str:
    response = transport.get(url, headers=headers, timeout=timeout)
    _raise_for_status(response)
    return response.body


def _raise_for_status(response: HTTPResponse) -> None:
    if 200 <= response.status_code < 300:
        return
    if response.status_code in {401, 403}:
        remaining = response.headers.get("x-ratelimit-remaining")
        if response.status_code == 403 and remaining == "0":
            raise ChangeRequestRateLimitError("Platform rate limit exceeded.")
        raise ChangeRequestAuthError("Platform authorization failed.")
    if response.status_code == 404:
        raise ChangeRequestNotFoundError("Change request not found.")
    raise ChangeRequestFetchError(f"Platform request failed with status {response.status_code}.")


def _github_files(payload: dict[str, Any] | list[Any]) -> list[ChangeRequestFile]:
    if not isinstance(payload, list):
        raise ChangeRequestFetchError("GitHub files response must be a list.")
    files: list[ChangeRequestFile] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        files.append(
            ChangeRequestFile(
                path=_str_or_empty(item.get("filename")),
                status=_str_or_empty(item.get("status")),
                additions=_int_or_zero(item.get("additions")),
                deletions=_int_or_zero(item.get("deletions")),
                patch=_optional_str(item.get("patch")),
            )
        )
    return files


def _github_commits(payload: dict[str, Any] | list[Any]) -> list[ChangeRequestCommit]:
    if not isinstance(payload, list):
        raise ChangeRequestFetchError("GitHub commits response must be a list.")
    commits: list[ChangeRequestCommit] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        commit = item.get("commit") if isinstance(item.get("commit"), dict) else {}
        author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
        message = _str_or_empty(commit.get("message"))
        commits.append(
            ChangeRequestCommit(
                sha=_str_or_empty(item.get("sha")),
                title=message.splitlines()[0] if message else "",
                author=_optional_str(author.get("name") if isinstance(author, dict) else None),
            )
        )
    return commits


def _gitee_diff_files(payload: dict[str, Any] | list[Any]) -> list[_DiffFile]:
    items = _list_payload(payload, "Gitee files response must be a list.")
    diff_files: list[_DiffFile] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        patch = _optional_str(item.get("patch")) or _optional_str(item.get("diff"))
        new_path = _first_present_str(
            item.get("filename"),
            item.get("new_path"),
            item.get("path"),
            item.get("file_name"),
        )
        old_path = _first_present_str(item.get("old_path"), new_path) or new_path
        if not new_path:
            continue
        additions, deletions = _line_counts(item, patch)
        file = ChangeRequestFile(
            path=new_path,
            status=_first_present_str(item.get("status"), item.get("state")) or "modified",
            additions=additions,
            deletions=deletions,
            patch=patch,
        )
        diff_files.append(_DiffFile(file=file, old_path=old_path, new_path=new_path))
    return diff_files


def _gitee_commits(payload: dict[str, Any] | list[Any]) -> list[ChangeRequestCommit]:
    items = _list_payload(payload, "Gitee commits response must be a list.")
    commits: list[ChangeRequestCommit] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        commit = item.get("commit") if isinstance(item.get("commit"), dict) else {}
        author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
        message = _first_present_str(
            commit.get("message") if isinstance(commit, dict) else None,
            item.get("message"),
            item.get("title"),
        )
        commits.append(
            ChangeRequestCommit(
                sha=_first_present_str(item.get("sha"), item.get("id")) or "",
                title=message.splitlines()[0] if message else "",
                author=_first_present_str(
                    author.get("name") if isinstance(author, dict) else None,
                    item.get("author_name"),
                    _nested_str(item, "author", "name"),
                ),
            )
        )
    return commits


def _gitlab_diff_files(payload: dict[str, Any] | list[Any]) -> list[_DiffFile]:
    items = _list_payload(payload, "GitLab diffs response must be a list.")
    diff_files: list[_DiffFile] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        patch = _optional_str(item.get("diff")) or _optional_str(item.get("patch"))
        new_path = _first_present_str(item.get("new_path"), item.get("path"))
        old_path = _first_present_str(item.get("old_path"), new_path) or new_path
        if not new_path:
            continue
        additions, deletions = _line_counts(item, patch)
        file = ChangeRequestFile(
            path=new_path,
            status=_gitlab_file_status(item),
            additions=additions,
            deletions=deletions,
            patch=patch,
        )
        diff_files.append(_DiffFile(file=file, old_path=old_path, new_path=new_path))
    return diff_files


def _gitlab_commits(payload: dict[str, Any] | list[Any]) -> list[ChangeRequestCommit]:
    items = _list_payload(payload, "GitLab commits response must be a list.")
    commits: list[ChangeRequestCommit] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        message = _first_present_str(item.get("title"), item.get("message"))
        commits.append(
            ChangeRequestCommit(
                sha=_first_present_str(item.get("id"), item.get("short_id")) or "",
                title=message.splitlines()[0] if message else "",
                author=_first_present_str(item.get("author_name"), _nested_str(item, "author", "name")),
            )
        )
    return commits


def _build_diff_text(files: list[_DiffFile]) -> str:
    parts: list[str] = []
    for item in files:
        patch = item.file.patch
        if not patch:
            continue
        patch = patch.rstrip()
        if patch.startswith("diff --git "):
            parts.append(patch)
            continue
        header = f"diff --git a/{item.old_path} b/{item.new_path}"
        if patch.startswith("--- "):
            parts.append(f"{header}\n{patch}")
        else:
            parts.append(f"{header}\n--- a/{item.old_path}\n+++ b/{item.new_path}\n{patch}")
    if not parts:
        raise ChangeRequestFetchError("Platform response did not include file patches.")
    return "\n".join(parts) + "\n"


def _line_counts(item: dict[str, Any], patch: str | None) -> tuple[int, int]:
    additions = _optional_int(
        item.get("additions")
        if "additions" in item
        else item.get("additions_count", item.get("added_lines"))
    )
    deletions = _optional_int(
        item.get("deletions")
        if "deletions" in item
        else item.get("deletions_count", item.get("removed_lines"))
    )
    if additions is not None and deletions is not None:
        return additions, deletions
    counted_additions, counted_deletions = _count_patch_lines(patch or "")
    return (
        additions if additions is not None else counted_additions,
        deletions if deletions is not None else counted_deletions,
    )


def _count_patch_lines(patch: str) -> tuple[int, int]:
    additions = 0
    deletions = 0
    for line in patch.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1
    return additions, deletions


def _gitlab_file_status(item: dict[str, Any]) -> str:
    if item.get("new_file") is True:
        return "added"
    if item.get("deleted_file") is True:
        return "removed"
    if item.get("renamed_file") is True:
        return "renamed"
    return "modified"


def _list_payload(payload: dict[str, Any] | list[Any], error: str) -> list[Any]:
    if not isinstance(payload, list):
        raise ChangeRequestFetchError(error)
    return payload


def _author_from_payload(payload: dict[str, Any]) -> str:
    author = payload.get("author") if isinstance(payload.get("author"), dict) else {}
    user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
    return (
        _first_present_str(
            author.get("username") if isinstance(author, dict) else None,
            author.get("login") if isinstance(author, dict) else None,
            author.get("name") if isinstance(author, dict) else None,
            user.get("login") if isinstance(user, dict) else None,
            user.get("username") if isinstance(user, dict) else None,
            user.get("name") if isinstance(user, dict) else None,
            payload.get("author_name"),
        )
        or ""
    )


def _parse_http_url(url: str):
    normalized = url.strip()
    if not normalized:
        raise ChangeRequestValidationError("PR/MR URL is required.")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ChangeRequestValidationError("PR/MR URL must be an http or https URL.")
    return parsed


def _path_parts(path: str) -> list[str]:
    return [part for part in path.strip("/").split("/") if part]


def _validate_number(number: str) -> None:
    if not number.isdigit():
        raise ChangeRequestValidationError("PR/MR number must be numeric.")


def _canonical_url(parsed) -> str:
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"


def _str_or_empty(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _int_or_zero(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _optional_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _first_present_str(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None


def _nested_str(payload: dict[str, Any], parent: str, child: str) -> str | None:
    value = payload.get(parent)
    if not isinstance(value, dict):
        return None
    return _optional_str(value.get(child))

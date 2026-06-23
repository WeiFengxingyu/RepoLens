import json

import pytest

from app.core.config import Settings
from app.services.change_request import (
    PLATFORM_GITEE,
    PLATFORM_GITLAB,
    PLATFORM_SELF_HOSTED_GITLAB,
    ChangeRequestAuthError,
    ChangeRequestDiffTooLargeError,
    ChangeRequestFetchError,
    ChangeRequestNotFoundError,
    ChangeRequestRateLimitError,
    GiteeChangeRequestProvider,
    GitLabChangeRequestProvider,
    HTTPResponse,
    parse_change_request_url,
)


def test_gitee_provider_fetches_metadata_files_commits_and_rebuilds_diff() -> None:
    transport = FakeTransport(
        {
            "https://gitee.com/api/v5/repos/team/demo/pulls/7?access_token=gitee-token": [
                _json_response(
                    {
                        "title": "Fix validation",
                        "author": {"login": "gitee-user"},
                        "state": "open",
                        "head": {"ref": "feature/gitee"},
                        "base": {"ref": "master"},
                        "html_url": "https://gitee.com/team/demo/pulls/7",
                    }
                )
            ],
            "https://gitee.com/api/v5/repos/team/demo/pulls/7/files?access_token=gitee-token": [
                _json_response(
                    [
                        {
                            "filename": "src/app.py",
                            "status": "modified",
                            "patch": "@@ -1 +1 @@\n-old()\n+new()\n",
                        }
                    ]
                )
            ],
            "https://gitee.com/api/v5/repos/team/demo/pulls/7/commits?access_token=gitee-token": [
                _json_response(
                    [
                        {
                            "sha": "gitee-sha",
                            "commit": {
                                "message": "Fix validation\n\nBody",
                                "author": {"name": "Lin"},
                            },
                        }
                    ]
                )
            ],
        }
    )
    provider = GiteeChangeRequestProvider(transport=transport)
    ref = parse_change_request_url("https://gitee.com/team/demo/pulls/7")

    change_request = provider.fetch(ref, Settings(gitee_token="gitee-token"))

    assert change_request.ref.platform == PLATFORM_GITEE
    assert change_request.title == "Fix validation"
    assert change_request.author == "gitee-user"
    assert change_request.source_branch == "feature/gitee"
    assert change_request.target_branch == "master"
    assert change_request.html_url == "https://gitee.com/team/demo/pulls/7"
    assert change_request.diff_text.startswith("diff --git a/src/app.py b/src/app.py")
    assert "+new()" in change_request.diff_text
    assert change_request.files[0].path == "src/app.py"
    assert change_request.files[0].additions == 1
    assert change_request.files[0].deletions == 1
    assert change_request.commits[0].sha == "gitee-sha"
    assert change_request.commits[0].title == "Fix validation"
    assert change_request.metadata == {
        "platform": "gitee",
        "api_source": "gitee_pulls",
        "changed_file_count": 1,
        "addition_count": 1,
        "deletion_count": 1,
        "commit_count": 1,
    }
    assert all("Authorization" not in call["headers"] for call in transport.calls)
    assert "gitee-token" not in str(change_request.metadata)


def test_gitlab_provider_fetches_gitlab_dot_com_merge_request() -> None:
    transport = FakeTransport(_gitlab_payload("https://gitlab.com/api/v4"))
    provider = GitLabChangeRequestProvider(transport=transport)
    ref = parse_change_request_url("https://gitlab.com/group/subgroup/demo/-/merge_requests/108")

    change_request = provider.fetch(ref, Settings(gitlab_token="gitlab-token"))

    assert change_request.ref.platform == PLATFORM_GITLAB
    assert change_request.title == "Fix GitLab flow"
    assert change_request.author == "gitlab-user"
    assert change_request.source_branch == "feature/gitlab"
    assert change_request.target_branch == "main"
    assert change_request.diff_text.startswith("diff --git a/src/app.ts b/src/app.ts")
    assert change_request.files[0].path == "src/app.ts"
    assert change_request.files[0].status == "modified"
    assert change_request.files[0].additions == 1
    assert change_request.files[0].deletions == 1
    assert change_request.commits[0].sha == "gitlab-sha"
    assert change_request.metadata["platform"] == PLATFORM_GITLAB
    assert all(call["headers"]["PRIVATE-TOKEN"] == "gitlab-token" for call in transport.calls)
    assert "gitlab-token" not in str(change_request.metadata)


def test_gitlab_provider_derives_self_hosted_api_base_from_merge_request_url() -> None:
    transport = FakeTransport(_gitlab_payload("https://git.example.com/api/v4"))
    provider = GitLabChangeRequestProvider(transport=transport)
    ref = parse_change_request_url("https://git.example.com/team/demo/-/merge_requests/5")

    change_request = provider.fetch(ref, Settings(gitlab_token="self-token"))

    assert change_request.ref.platform == PLATFORM_SELF_HOSTED_GITLAB
    assert change_request.metadata["platform"] == PLATFORM_SELF_HOSTED_GITLAB
    assert transport.calls[0]["url"].startswith(
        "https://git.example.com/api/v4/projects/team%2Fdemo/merge_requests/5"
    )


def test_gitlab_provider_allows_configured_self_hosted_api_base_override() -> None:
    transport = FakeTransport(_gitlab_payload("https://git.internal/api/v4"))
    provider = GitLabChangeRequestProvider(transport=transport)
    ref = parse_change_request_url("https://git.example.com/team/demo/-/merge_requests/5")

    provider.fetch(
        ref,
        Settings(
            gitlab_token="self-token",
            gitlab_base_url="https://git.internal/api/v4",
        ),
    )

    assert transport.calls[0]["url"].startswith(
        "https://git.internal/api/v4/projects/team%2Fdemo/merge_requests/5"
    )


def test_phase6_ext_providers_map_errors_and_diff_limits() -> None:
    gitee_ref = parse_change_request_url("https://gitee.com/team/demo/pulls/7")
    gitlab_ref = parse_change_request_url("https://gitlab.com/team/demo/-/merge_requests/7")

    with pytest.raises(ChangeRequestNotFoundError):
        GiteeChangeRequestProvider(
            transport=FakeTransport(
                {"https://gitee.com/api/v5/repos/team/demo/pulls/7": [_status_response(404)]}
            )
        ).fetch(gitee_ref, Settings())

    with pytest.raises(ChangeRequestAuthError):
        GitLabChangeRequestProvider(
            transport=FakeTransport(
                {
                    "https://gitlab.com/api/v4/projects/team%2Fdemo/merge_requests/7": [
                        _status_response(401)
                    ]
                }
            )
        ).fetch(gitlab_ref, Settings())

    with pytest.raises(ChangeRequestRateLimitError):
        GitLabChangeRequestProvider(
            transport=FakeTransport(
                {
                    "https://gitlab.com/api/v4/projects/team%2Fdemo/merge_requests/7": [
                        HTTPResponse(
                            status_code=403,
                            body='{"message":"rate limit"}',
                            headers={"x-ratelimit-remaining": "0"},
                        )
                    ]
                }
            )
        ).fetch(gitlab_ref, Settings())

    with pytest.raises(ChangeRequestDiffTooLargeError):
        GitLabChangeRequestProvider(
            transport=FakeTransport(
                _gitlab_payload("https://gitlab.com/api/v4", patch="+x\n" * 20)
            )
        ).fetch(gitlab_ref, Settings(change_request_max_diff_chars=10))

    with pytest.raises(ChangeRequestFetchError):
        GitLabChangeRequestProvider(
            transport=FakeTransport(_gitlab_payload("https://gitlab.com/api/v4", patch=""))
        ).fetch(gitlab_ref, Settings())


class FakeTransport:
    def __init__(self, responses):
        self.responses = {url: list(items) for url, items in responses.items()}
        self.calls = []

    def get(self, url, *, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        responses = self.responses[url]
        return responses.pop(0)


def _gitlab_payload(base_url: str, patch: str = "@@ -1 +1 @@\n-old()\n+new()\n"):
    return {
        f"{base_url}/projects/group%2Fsubgroup%2Fdemo/merge_requests/108": [
            _json_response(
                {
                    "title": "Fix GitLab flow",
                    "author": {"username": "gitlab-user"},
                    "state": "opened",
                    "source_branch": "feature/gitlab",
                    "target_branch": "main",
                    "web_url": "https://gitlab.com/group/subgroup/demo/-/merge_requests/108",
                }
            )
        ],
        f"{base_url}/projects/group%2Fsubgroup%2Fdemo/merge_requests/108/diffs": [
            _json_response(
                [
                    {
                        "old_path": "src/app.ts",
                        "new_path": "src/app.ts",
                        "new_file": False,
                        "renamed_file": False,
                        "deleted_file": False,
                        "diff": patch,
                    }
                ]
            )
        ],
        f"{base_url}/projects/group%2Fsubgroup%2Fdemo/merge_requests/108/commits": [
            _json_response(
                [
                    {
                        "id": "gitlab-sha",
                        "title": "Fix GitLab flow",
                        "author_name": "Grace",
                    }
                ]
            )
        ],
        f"{base_url}/projects/team%2Fdemo/merge_requests/5": [
            _json_response(
                {
                    "title": "Fix GitLab flow",
                    "author": {"username": "gitlab-user"},
                    "state": "opened",
                    "source_branch": "feature/gitlab",
                    "target_branch": "main",
                    "web_url": "https://git.example.com/team/demo/-/merge_requests/5",
                }
            )
        ],
        f"{base_url}/projects/team%2Fdemo/merge_requests/5/diffs": [
            _json_response(
                [
                    {
                        "old_path": "src/app.ts",
                        "new_path": "src/app.ts",
                        "diff": patch,
                    }
                ]
            )
        ],
        f"{base_url}/projects/team%2Fdemo/merge_requests/5/commits": [
            _json_response(
                [
                    {
                        "id": "gitlab-sha",
                        "title": "Fix GitLab flow",
                        "author_name": "Grace",
                    }
                ]
            )
        ],
        f"{base_url}/projects/team%2Fdemo/merge_requests/7": [
            _json_response(
                {
                    "title": "Fix GitLab flow",
                    "author": {"username": "gitlab-user"},
                    "state": "opened",
                    "source_branch": "feature/gitlab",
                    "target_branch": "main",
                    "web_url": "https://gitlab.com/team/demo/-/merge_requests/7",
                }
            )
        ],
        f"{base_url}/projects/team%2Fdemo/merge_requests/7/diffs": [
            _json_response(
                [
                    {
                        "old_path": "src/app.ts",
                        "new_path": "src/app.ts",
                        "diff": patch,
                    }
                ]
            )
        ],
        f"{base_url}/projects/team%2Fdemo/merge_requests/7/commits": [
            _json_response(
                [
                    {
                        "id": "gitlab-sha",
                        "title": "Fix GitLab flow",
                        "author_name": "Grace",
                    }
                ]
            )
        ],
    }


def _json_response(payload) -> HTTPResponse:
    return HTTPResponse(status_code=200, body=json.dumps(payload), headers={})


def _status_response(status_code: int) -> HTTPResponse:
    return HTTPResponse(status_code=status_code, body="{}", headers={})

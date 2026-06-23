import json

import pytest

from app.core.config import Settings
from app.services.change_request import (
    ChangeRequestAuthError,
    ChangeRequestDiffTooLargeError,
    ChangeRequestNotFoundError,
    ChangeRequestRateLimitError,
    GitHubChangeRequestProvider,
    HTTPResponse,
    parse_change_request_url,
)


def test_github_provider_fetches_metadata_files_commits_and_diff() -> None:
    transport = FakeTransport(
        {
            "https://api.github.com/repos/openai/repolens/pulls/42": [
                _json_response(
                    {
                        "title": "Improve review flow",
                        "user": {"login": "octocat"},
                        "state": "open",
                        "head": {"ref": "feature/pr-review"},
                        "base": {"ref": "main"},
                        "html_url": "https://github.com/openai/repolens/pull/42",
                    }
                ),
                HTTPResponse(
                    status_code=200,
                    body="diff --git a/app.py b/app.py\n+print('hi')\n",
                    headers={},
                ),
            ],
            "https://api.github.com/repos/openai/repolens/pulls/42/files": [
                _json_response(
                    [
                        {
                            "filename": "app.py",
                            "status": "modified",
                            "additions": 2,
                            "deletions": 1,
                            "patch": "@@ -1 +1 @@",
                        }
                    ]
                )
            ],
            "https://api.github.com/repos/openai/repolens/pulls/42/commits": [
                _json_response(
                    [
                        {
                            "sha": "abc123",
                            "commit": {
                                "message": "Improve review flow\n\nDetails",
                                "author": {"name": "Ada"},
                            },
                        }
                    ]
                )
            ],
        }
    )
    provider = GitHubChangeRequestProvider(transport=transport)
    ref = parse_change_request_url("https://github.com/openai/repolens/pull/42")
    settings = Settings(github_token="secret-token")

    change_request = provider.fetch(ref, settings)

    assert change_request.title == "Improve review flow"
    assert change_request.author == "octocat"
    assert change_request.source_branch == "feature/pr-review"
    assert change_request.target_branch == "main"
    assert change_request.state == "open"
    assert change_request.diff_text.startswith("diff --git")
    assert change_request.files[0].path == "app.py"
    assert change_request.files[0].additions == 2
    assert change_request.commits[0].sha == "abc123"
    assert change_request.commits[0].title == "Improve review flow"
    assert change_request.commits[0].author == "Ada"
    assert change_request.metadata == {
        "platform": "github",
        "api_source": "github_pulls",
        "changed_file_count": 1,
        "addition_count": 2,
        "deletion_count": 1,
        "commit_count": 1,
    }
    assert all(call["headers"]["Authorization"] == "Bearer secret-token" for call in transport.calls)
    assert all("secret-token" not in str(change_request.metadata) for _ in [0])


def test_github_provider_allows_public_requests_without_token() -> None:
    transport = FakeTransport(_success_payload())
    provider = GitHubChangeRequestProvider(transport=transport)
    ref = parse_change_request_url("https://github.com/openai/repolens/pull/42")

    provider.fetch(ref, Settings(github_token=""))

    assert all("Authorization" not in call["headers"] for call in transport.calls)


def test_github_provider_maps_not_found_auth_and_rate_limit_errors() -> None:
    ref = parse_change_request_url("https://github.com/openai/repolens/pull/42")

    with pytest.raises(ChangeRequestNotFoundError):
        GitHubChangeRequestProvider(
            transport=FakeTransport(
                {"https://api.github.com/repos/openai/repolens/pulls/42": [_status_response(404)]}
            )
        ).fetch(ref, Settings())

    with pytest.raises(ChangeRequestAuthError):
        GitHubChangeRequestProvider(
            transport=FakeTransport(
                {"https://api.github.com/repos/openai/repolens/pulls/42": [_status_response(401)]}
            )
        ).fetch(ref, Settings())

    with pytest.raises(ChangeRequestRateLimitError):
        GitHubChangeRequestProvider(
            transport=FakeTransport(
                {
                    "https://api.github.com/repos/openai/repolens/pulls/42": [
                        HTTPResponse(
                            status_code=403,
                            body='{"message":"rate limit"}',
                            headers={"x-ratelimit-remaining": "0"},
                        )
                    ]
                }
            )
        ).fetch(ref, Settings())


def test_github_provider_rejects_diff_over_configured_limit() -> None:
    transport = FakeTransport(_success_payload(diff_text="x" * 20))
    provider = GitHubChangeRequestProvider(transport=transport)
    ref = parse_change_request_url("https://github.com/openai/repolens/pull/42")

    with pytest.raises(ChangeRequestDiffTooLargeError):
        provider.fetch(ref, Settings(change_request_max_diff_chars=10))


class FakeTransport:
    def __init__(self, responses):
        self.responses = {url: list(items) for url, items in responses.items()}
        self.calls = []

    def get(self, url, *, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        responses = self.responses[url]
        return responses.pop(0)


def _json_response(payload) -> HTTPResponse:
    return HTTPResponse(status_code=200, body=json.dumps(payload), headers={})


def _status_response(status_code: int) -> HTTPResponse:
    return HTTPResponse(status_code=status_code, body="{}", headers={})


def _success_payload(diff_text: str = "diff --git a/app.py b/app.py\n+print('hi')\n"):
    return {
        "https://api.github.com/repos/openai/repolens/pulls/42": [
            _json_response(
                {
                    "title": "Improve review flow",
                    "user": {"login": "octocat"},
                    "state": "open",
                    "head": {"ref": "feature/pr-review"},
                    "base": {"ref": "main"},
                    "html_url": "https://github.com/openai/repolens/pull/42",
                }
            ),
            HTTPResponse(status_code=200, body=diff_text, headers={}),
        ],
        "https://api.github.com/repos/openai/repolens/pulls/42/files": [
            _json_response(
                [
                    {
                        "filename": "app.py",
                        "status": "modified",
                        "additions": 2,
                        "deletions": 1,
                    }
                ]
            )
        ],
        "https://api.github.com/repos/openai/repolens/pulls/42/commits": [
            _json_response(
                [
                    {
                        "sha": "abc123",
                        "commit": {
                            "message": "Improve review flow",
                            "author": {"name": "Ada"},
                        },
                    }
                ]
            )
        ],
    }

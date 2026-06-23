import pytest

from app.services.change_request import (
    CHANGE_TYPE_MERGE_REQUEST,
    CHANGE_TYPE_PULL_REQUEST,
    PLATFORM_GITEE,
    PLATFORM_GITHUB,
    PLATFORM_GITLAB,
    PLATFORM_SELF_HOSTED_GITLAB,
    ChangeRequestValidationError,
    GiteeChangeRequestProvider,
    GitHubChangeRequestProvider,
    GitLabChangeRequestProvider,
    UnsupportedChangeRequestProviderError,
    choose_change_request_provider,
    parse_change_request_url,
)


def test_parse_github_pull_request_url() -> None:
    ref = parse_change_request_url("https://github.com/openai/repolens/pull/42?tab=files")

    assert ref.platform == PLATFORM_GITHUB
    assert ref.change_type == CHANGE_TYPE_PULL_REQUEST
    assert ref.owner == "openai"
    assert ref.repo == "repolens"
    assert ref.number == "42"
    assert ref.url == "https://github.com/openai/repolens/pull/42"
    assert ref.base_url == "https://github.com"


def test_parse_gitee_pull_request_url() -> None:
    ref = parse_change_request_url("https://gitee.com/team/demo-repo/pulls/7")

    assert ref.platform == PLATFORM_GITEE
    assert ref.change_type == CHANGE_TYPE_PULL_REQUEST
    assert ref.owner == "team"
    assert ref.repo == "demo-repo"
    assert ref.number == "7"
    assert ref.base_url == "https://gitee.com"


def test_parse_gitlab_merge_request_url_with_nested_namespace() -> None:
    ref = parse_change_request_url(
        "https://gitlab.com/group/subgroup/demo/-/merge_requests/108#note"
    )

    assert ref.platform == PLATFORM_GITLAB
    assert ref.change_type == CHANGE_TYPE_MERGE_REQUEST
    assert ref.owner == "group/subgroup"
    assert ref.repo == "demo"
    assert ref.number == "108"
    assert ref.url == "https://gitlab.com/group/subgroup/demo/-/merge_requests/108"
    assert ref.base_url == "https://gitlab.com"


def test_parse_self_hosted_gitlab_merge_request_url() -> None:
    ref = parse_change_request_url("https://git.example.com/team/demo/-/merge_requests/5")

    assert ref.platform == PLATFORM_SELF_HOSTED_GITLAB
    assert ref.change_type == CHANGE_TYPE_MERGE_REQUEST
    assert ref.owner == "team"
    assert ref.repo == "demo"
    assert ref.number == "5"
    assert ref.base_url == "https://git.example.com"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "ssh://github.com/openai/repolens/pull/42",
        "https://github.com/openai/repolens/pull/not-number",
        "https://gitlab.com/group/demo/merge_requests/1",
        "https://gitlab.com/demo/-/merge_requests/1",
    ],
)
def test_parse_change_request_url_rejects_invalid_urls(url: str) -> None:
    with pytest.raises((ChangeRequestValidationError, UnsupportedChangeRequestProviderError)):
        parse_change_request_url(url)


def test_choose_change_request_provider_returns_expected_provider() -> None:
    assert isinstance(
        choose_change_request_provider("https://github.com/a/b/pull/1"),
        GitHubChangeRequestProvider,
    )
    assert isinstance(
        choose_change_request_provider("https://gitee.com/a/b/pulls/1"),
        GiteeChangeRequestProvider,
    )
    assert isinstance(
        choose_change_request_provider("https://gitlab.com/a/b/-/merge_requests/1"),
        GitLabChangeRequestProvider,
    )


def test_choose_change_request_provider_rejects_unsupported_provider() -> None:
    with pytest.raises(UnsupportedChangeRequestProviderError):
        choose_change_request_provider("https://example.com/a/b/pull/1")


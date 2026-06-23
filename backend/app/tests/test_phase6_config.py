from app.core.config import Settings


def test_phase6_change_request_settings_use_safe_defaults() -> None:
    settings = Settings()

    assert settings.change_request_timeout_seconds == 30.0
    assert settings.change_request_max_diff_chars == 200_000
    assert settings.github_token == ""
    assert settings.github_base_url == "https://api.github.com"
    assert settings.gitee_token == ""
    assert settings.gitee_base_url == "https://gitee.com/api/v5"
    assert settings.gitlab_token == ""
    assert settings.gitlab_base_url == "https://gitlab.com/api/v4"


def test_phase6_change_request_settings_can_be_overridden() -> None:
    settings = Settings(
        change_request_timeout_seconds=12.5,
        change_request_max_diff_chars=12345,
        github_token="github-secret",
        github_base_url="https://github.enterprise.example/api/v3",
        gitee_token="gitee-secret",
        gitee_base_url="https://gitee.example/api/v5",
        gitlab_token="gitlab-secret",
        gitlab_base_url="https://gitlab.example/api/v4",
    )

    assert settings.change_request_timeout_seconds == 12.5
    assert settings.change_request_max_diff_chars == 12345
    assert settings.github_token == "github-secret"
    assert settings.github_base_url == "https://github.enterprise.example/api/v3"
    assert settings.gitee_token == "gitee-secret"
    assert settings.gitee_base_url == "https://gitee.example/api/v5"
    assert settings.gitlab_token == "gitlab-secret"
    assert settings.gitlab_base_url == "https://gitlab.example/api/v4"

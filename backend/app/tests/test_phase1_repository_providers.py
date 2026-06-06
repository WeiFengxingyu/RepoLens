from pathlib import Path

import pytest

from app.models import RepositorySourceType
from app.services.repository import (
    GenericGitProvider,
    LocalRepositoryProvider,
    ProviderError,
    choose_provider,
    detect_git_source_type,
)


def test_local_repository_provider_accepts_existing_directory(tmp_path: Path) -> None:
    provider = LocalRepositoryProvider()

    assert provider.detect(str(tmp_path))
    assert provider.validate(str(tmp_path)).valid

    prepared = provider.prepare(str(tmp_path), tmp_path / "unused", None)

    assert prepared.source_type == RepositorySourceType.LOCAL.value
    assert prepared.local_path == tmp_path.resolve()


def test_local_repository_provider_rejects_missing_path(tmp_path: Path) -> None:
    provider = LocalRepositoryProvider()
    missing = tmp_path / "missing"

    assert not provider.detect(str(missing))
    assert not provider.validate(str(missing)).valid

    with pytest.raises(ProviderError):
        provider.prepare(str(missing), tmp_path / "unused", None)


@pytest.mark.parametrize(
    ("url", "source_type"),
    [
        ("https://github.com/owner/repo.git", RepositorySourceType.GITHUB.value),
        ("https://gitee.com/owner/repo.git", RepositorySourceType.GITEE.value),
        ("https://gitlab.com/owner/repo.git", RepositorySourceType.GITLAB.value),
        ("git@github.com:owner/repo.git", RepositorySourceType.GITHUB.value),
        ("https://example.com/owner/repo.git", RepositorySourceType.GENERIC_GIT.value),
    ],
)
def test_generic_git_provider_detects_supported_git_urls(url: str, source_type: str) -> None:
    provider = GenericGitProvider()

    assert provider.detect(url)
    assert provider.validate(url).valid
    assert detect_git_source_type(url) == source_type


def test_choose_provider_prefers_local_for_existing_path(tmp_path: Path) -> None:
    provider = choose_provider(str(tmp_path))

    assert isinstance(provider, LocalRepositoryProvider)


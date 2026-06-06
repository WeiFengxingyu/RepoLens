from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from app.models import RepositorySourceType


class ProviderError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderValidationResult:
    valid: bool
    reason: str | None = None


@dataclass(frozen=True)
class PreparedRepository:
    source_type: str
    source_url: str | None
    local_path: Path
    branch: str | None = None
    commit_hash: str | None = None


@dataclass(frozen=True)
class RepositorySourceMetadata:
    name: str
    source_type: str


class RepositoryProvider:
    def detect(self, source: str) -> bool:
        raise NotImplementedError

    def validate(self, source: str) -> ProviderValidationResult:
        raise NotImplementedError

    def prepare(self, source: str, target_dir: Path, branch: str | None) -> PreparedRepository:
        raise NotImplementedError

    def get_metadata(self, source: str) -> RepositorySourceMetadata:
        raise NotImplementedError


class LocalRepositoryProvider(RepositoryProvider):
    def detect(self, source: str) -> bool:
        return Path(source).expanduser().exists()

    def validate(self, source: str) -> ProviderValidationResult:
        path = Path(source).expanduser()
        if not path.exists():
            return ProviderValidationResult(False, "Path does not exist.")
        if not path.is_dir():
            return ProviderValidationResult(False, "Path is not a directory.")
        return ProviderValidationResult(True)

    def prepare(self, source: str, target_dir: Path, branch: str | None) -> PreparedRepository:
        validation = self.validate(source)
        if not validation.valid:
            raise ProviderError(validation.reason or "Invalid local repository path.")

        path = Path(source).expanduser().resolve()
        return PreparedRepository(
            source_type=RepositorySourceType.LOCAL.value,
            source_url=None,
            local_path=path,
            branch=_read_git_branch(path) or branch,
            commit_hash=_read_git_commit(path),
        )

    def get_metadata(self, source: str) -> RepositorySourceMetadata:
        path = Path(source).expanduser()
        return RepositorySourceMetadata(
            name=path.resolve().name,
            source_type=RepositorySourceType.LOCAL.value,
        )


class GenericGitProvider(RepositoryProvider):
    HTTPS_GIT_RE = re.compile(r"^https?://[^/]+/.+/.+(?:\.git)?$")
    SSH_GIT_RE = re.compile(r"^git@[^:]+:.+/.+(?:\.git)?$")

    def detect(self, source: str) -> bool:
        return bool(self.HTTPS_GIT_RE.match(source) or self.SSH_GIT_RE.match(source))

    def validate(self, source: str) -> ProviderValidationResult:
        if self.detect(source):
            return ProviderValidationResult(True)
        return ProviderValidationResult(False, "Source is not a supported Git URL.")

    def prepare(self, source: str, target_dir: Path, branch: str | None) -> PreparedRepository:
        validation = self.validate(source)
        if not validation.valid:
            raise ProviderError(validation.reason or "Invalid Git URL.")

        target_dir.mkdir(parents=True, exist_ok=True)
        command = ["git", "clone", "--depth", "1"]
        if branch:
            command.extend(["--branch", branch])
        command.extend([source, str(target_dir)])

        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "git clone failed."
            raise ProviderError(message)

        return PreparedRepository(
            source_type=detect_git_source_type(source),
            source_url=source,
            local_path=target_dir.resolve(),
            branch=_read_git_branch(target_dir) or branch,
            commit_hash=_read_git_commit(target_dir),
        )

    def get_metadata(self, source: str) -> RepositorySourceMetadata:
        name = source.rstrip("/").removesuffix(".git").split("/")[-1]
        if ":" in name:
            name = name.split(":")[-1]
        return RepositorySourceMetadata(
            name=name,
            source_type=detect_git_source_type(source),
        )


def detect_git_source_type(source: str) -> str:
    lowered = source.lower()
    if "github.com" in lowered:
        return RepositorySourceType.GITHUB.value
    if "gitee.com" in lowered:
        return RepositorySourceType.GITEE.value
    if "gitlab" in lowered:
        return RepositorySourceType.GITLAB.value
    return RepositorySourceType.GENERIC_GIT.value


def choose_provider(source: str) -> RepositoryProvider:
    providers: list[RepositoryProvider] = [
        LocalRepositoryProvider(),
        GenericGitProvider(),
    ]
    for provider in providers:
        if provider.detect(source):
            return provider
    raise ProviderError("Source is neither an existing local path nor a supported Git URL.")


def _read_git_branch(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(path), "branch", "--show-current"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    branch = result.stdout.strip()
    return branch or None


def _read_git_commit(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    commit_hash = result.stdout.strip()
    return commit_hash or None


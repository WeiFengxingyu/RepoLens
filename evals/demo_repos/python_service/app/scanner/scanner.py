from pathlib import Path

from app.scanner.filters import should_skip_path


def scan_repository(root: str) -> list[str]:
    files: list[str] = []
    for path in Path(root).rglob("*"):
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if not should_skip_path(relative):
                files.append(relative)
    return sorted(files)

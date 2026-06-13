def should_skip_path(path: str) -> bool:
    blocked = {".git", "node_modules", ".venv", "__pycache__", ".env"}
    return any(part in blocked for part in path.split("/"))

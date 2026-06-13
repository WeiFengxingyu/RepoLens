from app.services.repositories import RepositoryImportService


import_service = RepositoryImportService()


def import_repository(payload: dict[str, str]) -> dict[str, object]:
    """Import a repository from a request payload."""
    source = payload.get("source", "")
    return import_service.import_repository(source)

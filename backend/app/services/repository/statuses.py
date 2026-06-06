from app.models import RepositoryStatus

TERMINAL_STATUSES = {
    RepositoryStatus.READY.value,
    RepositoryStatus.FAILED.value,
}


from app.audit.logger import AuditLogger
from app.services.tasks import TaskService


def schedule_daily_jobs(task_service: TaskService | None = None, audit_logger: AuditLogger | None = None) -> list[str]:
    service = task_service or TaskService()
    logger = audit_logger or AuditLogger()
    closed = service.close_overdue_tasks()
    logger.record_event("system", "daily_jobs.completed", {"closed_tasks": str(closed)})
    return ["close_overdue_tasks", "write_audit_summary"]

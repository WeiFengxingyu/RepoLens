from app.audit.logger import AuditLogger
from app.repositories.tasks import TaskRepository


class TaskService:
    def __init__(
        self,
        repository: TaskRepository | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.repository = repository or TaskRepository()
        self.audit_logger = audit_logger or AuditLogger()

    def create_task(self, title: str, owner_id: str) -> dict[str, str]:
        if not title:
            raise ValueError("title is required")
        task = self.repository.save_task({"title": title, "owner_id": owner_id, "status": "open"})
        self.audit_logger.record_event(owner_id, "task.created", {"task_id": task["id"]})
        return task

    def close_overdue_tasks(self) -> int:
        tasks = self.repository.list_open_tasks()
        closed = 0
        for task in tasks:
            if task.get("overdue") == "true":
                self.repository.update_status(task["id"], "closed")
                closed += 1
        return closed

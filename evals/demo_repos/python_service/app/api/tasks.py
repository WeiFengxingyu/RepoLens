from app.services.tasks import TaskService


task_service = TaskService()


def create_task(payload: dict[str, str]) -> dict[str, str]:
    """Create a task from an API request payload."""
    title = payload.get("title", "").strip()
    owner_id = payload.get("owner_id", "").strip()
    task = task_service.create_task(title=title, owner_id=owner_id)
    return {"id": task["id"], "title": task["title"], "status": task["status"]}

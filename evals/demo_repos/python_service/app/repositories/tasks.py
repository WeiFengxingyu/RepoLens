class TaskRepository:
    def __init__(self) -> None:
        self.tasks: dict[str, dict[str, str]] = {}

    def save_task(self, task: dict[str, str]) -> dict[str, str]:
        task_id = f"task-{len(self.tasks) + 1}"
        saved = {"id": task_id, **task}
        self.tasks[task_id] = saved
        return saved

    def list_open_tasks(self) -> list[dict[str, str]]:
        return [task for task in self.tasks.values() if task.get("status") == "open"]

    def update_status(self, task_id: str, status: str) -> None:
        self.tasks[task_id]["status"] = status

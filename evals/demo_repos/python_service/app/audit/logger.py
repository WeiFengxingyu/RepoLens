class MemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def write(self, payload: dict[str, object]) -> None:
        self.events.append(payload)


class AuditLogger:
    def __init__(self, sink: MemoryAuditSink | None = None) -> None:
        self.sink = sink or MemoryAuditSink()
        self.last_event: dict[str, object] | None = None

    def record_event(self, actor_id: str, action: str, metadata: dict[str, str]) -> None:
        payload = {"actor_id": actor_id, "action": action, "metadata": metadata}
        self.sink.write(payload)
        self.last_event = payload

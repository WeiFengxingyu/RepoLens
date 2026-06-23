from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import (
    CodeChunk,
    CodeRelation,
    RelationType,
    Repository,
    RepositoryStatus,
    SymbolType,
    Task,
    TaskType,
    ToolCall,
)
from app.services.tools import DIFF_MAX_CHARS


def test_mcp_initialize_and_tools_list() -> None:
    app = create_app()
    client = TestClient(app)

    initialize = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": {}},
    )
    tools = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": "tools", "method": "tools/list", "params": {}},
    )

    assert initialize.status_code == 200
    assert initialize.json()["result"]["serverInfo"]["name"] == "repolens"
    assert tools.status_code == 200
    tool_names = {tool["name"] for tool in tools.json()["result"]["tools"]}
    assert {
        "repository.list",
        "repository.status",
        "code.search",
        "file.read_slice",
        "symbol.context",
        "diff.analyze",
        "repository.ask",
        "review.diff",
    }.issubset(tool_names)


def test_mcp_code_search_and_file_read_slice_write_audit(monkeypatch, tmp_path: Path) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / "app.py").write_text(
        "def main():\n    return helper()\n\ndef helper():\n    return 2\n",
        encoding="utf-8",
    )

    with TestingSessionLocal() as db:
        repository_id = _insert_mcp_fixture(db, repository_root)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    search_response = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "search",
            "method": "tools/call",
            "params": {
                "name": "code.search",
                "arguments": {
                    "repository_id": repository_id,
                    "query": "main helper",
                    "top_k": 5,
                    "use_vector": False,
                },
                "client": {"name": "phase7-smoke"},
                "session_id": "session-1",
            },
        },
    )
    read_response = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "read",
            "method": "tools/call",
            "params": {
                "name": "file.read_slice",
                "arguments": {
                    "repository_id": repository_id,
                    "file_path": "app.py",
                    "start_line": 1,
                    "end_line": 2,
                },
                "client_name": "phase7-smoke",
                "client_session_id": "session-1",
            },
        },
    )

    assert search_response.status_code == 200
    search_body = search_response.json()
    assert search_body["result"]["isError"] is False
    assert search_body["result"]["structuredContent"]["repository_id"] == repository_id
    assert search_body["result"]["structuredContent"]["evidences"]

    assert read_response.status_code == 200
    read_body = read_response.json()
    assert read_body["result"]["structuredContent"]["content"] == "def main():\n    return helper()"

    audit_response = client.get("/api/mcp/tool-calls")
    assert audit_response.status_code == 200
    audits = audit_response.json()
    audited_tools = {item["tool_name"] for item in audits}
    assert {"code.search", "file.read_slice"}.issubset(audited_tools)
    assert all(item["client_name"] == "phase7-smoke" for item in audits[:2])
    assert all(item["client_session_id"] == "session-1" for item in audits[:2])
    assert all(item["permission_policy"] == "read_only" for item in audits[:2])
    assert all(item["input_hash"] for item in audits[:2])
    assert all(item["output_hash"] for item in audits[:2])

    with TestingSessionLocal() as db:
        tasks = db.scalars(select(Task).where(Task.task_type == TaskType.MCP_TOOL.value)).all()
        tool_calls = db.scalars(select(ToolCall)).all()

    assert len(tasks) == 2
    assert len(tool_calls) == 2
    assert {tool_call.permission_policy for tool_call in tool_calls} == {"read_only"}


def test_mcp_status_symbol_diff_ask_and_review_tools_smoke(monkeypatch, tmp_path: Path) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / "app.py").write_text(
        "def main():\n    return helper()\n\ndef helper():\n    return 2\n",
        encoding="utf-8",
    )

    with TestingSessionLocal() as db:
        repository_id = _insert_mcp_fixture(db, repository_root)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)
    diff_text = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def main():
-    return helper()
+    return helper() + 1
"""

    status = _call_mcp_tool(
        client,
        "repository.status",
        {"repository_id": repository_id},
        request_id="status",
    )
    symbol = _call_mcp_tool(
        client,
        "symbol.context",
        {"repository_id": repository_id, "symbol_name": "main", "max_neighbors": 5},
        request_id="symbol",
    )
    diff = _call_mcp_tool(
        client,
        "diff.analyze",
        {"repository_id": repository_id, "diff_text": diff_text},
        request_id="diff",
    )
    ask = _call_mcp_tool(
        client,
        "repository.ask",
        {
            "repository_id": repository_id,
            "question": "What does main call?",
            "top_k": 3,
            "use_vector": False,
        },
        request_id="ask",
    )
    review = _call_mcp_tool(
        client,
        "review.diff",
        {
            "repository_id": repository_id,
            "diff_text": diff_text,
            "top_k": 3,
            "use_vector": False,
            "run_static_check": False,
        },
        request_id="review",
    )

    assert status["structuredContent"]["status"] == RepositoryStatus.READY.value
    assert symbol["structuredContent"]["symbol"]["symbol_name"] == "main"
    assert symbol["structuredContent"]["neighbors"]
    assert diff["structuredContent"]["file_count"] == 1
    assert ask["structuredContent"]["status"] == "completed"
    assert review["structuredContent"]["status"] == "completed"

    with TestingSessionLocal() as db:
        tool_names = {
            tool_call.tool_name for tool_call in db.scalars(select(ToolCall)).all()
        }

    assert {
        "repository.status",
        "symbol.context",
        "diff.analyze",
        "repository.ask",
        "review.diff",
    }.issubset(tool_names)


def test_mcp_disabled_tool_and_file_security_are_reported_and_audited(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / ".env").write_text("SECRET=value\n", encoding="utf-8")
    (repository_root / "app.py").write_text("print('ok')\n", encoding="utf-8")

    with TestingSessionLocal() as db:
        repository_id = _insert_mcp_fixture(db, repository_root)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    disabled = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "disabled",
            "method": "tools/call",
            "params": {
                "name": "run_safe_static_check",
                "arguments": {
                    "repository_id": repository_id,
                    "checker": "python_ast_parse",
                    "file_paths": ["app.py"],
                },
            },
        },
    )
    sensitive = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "sensitive",
            "method": "tools/call",
            "params": {
                "name": "file.read_slice",
                "arguments": {
                    "repository_id": repository_id,
                    "file_path": ".env",
                    "start_line": 1,
                    "end_line": 1,
                },
            },
        },
    )
    traversal = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "traversal",
            "method": "tools/call",
            "params": {
                "name": "file.read_slice",
                "arguments": {
                    "repository_id": repository_id,
                    "file_path": "../outside.py",
                    "start_line": 1,
                    "end_line": 1,
                },
            },
        },
    )
    oversized = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "oversized",
            "method": "tools/call",
            "params": {
                "name": "review.diff",
                "arguments": {
                    "repository_id": repository_id,
                    "diff_text": "x" * (DIFF_MAX_CHARS + 1),
                },
            },
        },
    )

    assert disabled.status_code == 200
    assert disabled.json()["result"]["isError"] is True
    assert disabled.json()["result"]["structuredContent"]["permission_decision"] == "disabled"

    assert sensitive.status_code == 200
    assert sensitive.json()["error"]["code"] == -32000
    assert "Sensitive files are not allowed" in sensitive.json()["error"]["message"]

    assert traversal.status_code == 200
    assert traversal.json()["error"]["code"] == -32000
    assert "Path traversal is not allowed" in traversal.json()["error"]["message"]

    assert oversized.status_code == 200
    assert oversized.json()["error"]["code"] == -32000
    assert "String should have at most" in oversized.json()["error"]["message"]

    with TestingSessionLocal() as db:
        tool_calls = db.scalars(select(ToolCall).order_by(ToolCall.created_at)).all()

    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "run_safe_static_check",
        "file.read_slice",
        "file.read_slice",
        "review.diff",
    ]
    assert tool_calls[0].status == "disabled"
    assert tool_calls[0].permission_decision == "disabled"
    assert tool_calls[1].status == "failed"
    assert tool_calls[1].permission_decision == "allow"
    assert tool_calls[2].status == "failed"
    assert tool_calls[3].status == "failed"


def test_mcp_registry_metadata_endpoint() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/mcp/tools")

    assert response.status_code == 200
    tools = response.json()
    code_search = next(tool for tool in tools if tool["name"] == "code.search")
    assert code_search["permission_policy"] == "read_only"
    assert code_search["enabled"] is True


def _insert_mcp_fixture(db: Session, repository_root: Path) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path=str(repository_root),
        status=RepositoryStatus.READY.value,
        file_count=1,
        parsed_file_count=1,
        chunk_count=2,
        relation_count=1,
    )
    db.add(repository)
    db.flush()

    main_chunk = CodeChunk(
        repository_id=repository.id,
        file_path="app.py",
        language="python",
        symbol_name="main",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=1,
        end_line=2,
        content_hash="hash-main",
        content="def main():\n    return helper()\n",
    )
    helper_chunk = CodeChunk(
        repository_id=repository.id,
        file_path="app.py",
        language="python",
        symbol_name="helper",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=4,
        end_line=5,
        content_hash="hash-helper",
        content="def helper():\n    return 2\n",
    )
    db.add_all([main_chunk, helper_chunk])
    db.flush()
    db.add(
        CodeRelation(
            repository_id=repository.id,
            source_id=main_chunk.id,
            target_id=helper_chunk.id,
            source_symbol="main",
            target_symbol="helper",
            relation_type=RelationType.CALLS.value,
            source_file="app.py",
            target_file="app.py",
        )
    )
    db.commit()
    return repository.id


def _override_get_db(TestingSessionLocal):
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override_get_db


def _clear_embedding_env(monkeypatch) -> None:
    monkeypatch.delenv("REPOLENS_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_DIMENSION", raising=False)
    get_settings.cache_clear()


def _call_mcp_tool(
    client: TestClient,
    name: str,
    arguments: dict[str, object],
    *,
    request_id: str,
) -> dict[str, object]:
    response = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
                "client": {"name": "phase7-full-smoke"},
                "session_id": "session-full",
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("error") is None
    assert body["result"]["isError"] is False
    return body["result"]

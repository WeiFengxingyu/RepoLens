from app.services.mcp import build_default_registry


def test_mcp_registry_exposes_expected_tools_and_permissions() -> None:
    registry = build_default_registry()

    tools = {tool.name: tool for tool in registry.list_tools()}

    assert tools["repository.list"].permission_policy == "read_only"
    assert tools["repository.status"].permission_policy == "read_only"
    assert tools["code.search"].permission_policy == "read_only"
    assert tools["file.read_slice"].permission_policy == "read_only"
    assert tools["symbol.context"].permission_policy == "read_only"
    assert tools["diff.analyze"].permission_policy == "read_only"
    assert tools["repository.ask"].permission_policy == "read_only"
    assert tools["review.diff"].permission_policy == "read_only"
    assert tools["run_safe_static_check"].permission_policy == "safe_check"
    assert tools["run_safe_static_check"].enabled is False


def test_mcp_registry_tool_schema_is_mcp_compatible() -> None:
    registry = build_default_registry()
    code_search = registry.get("code.search").to_mcp_tool()

    assert code_search["name"] == "code.search"
    assert code_search["inputSchema"]["type"] == "object"
    assert "repository_id" in code_search["inputSchema"]["required"]
    assert code_search["annotations"]["permission_policy"] == "read_only"

package com.repolens.mcp.application;

public record McpRegisteredTool(
        McpToolDefinition definition,
        McpToolHandler handler
) {
}

package com.repolens.mcp.application;

import java.util.Map;

public record McpToolExecutionContext(
        McpToolDefinition definition,
        Map<String, Object> arguments
) {
}

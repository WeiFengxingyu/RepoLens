package com.repolens.mcp.application;

import java.util.Map;

public record McpToolDefinition(
        String name,
        String description,
        Map<String, Object> inputSchema,
        String permissionPolicy,
        boolean enabled
) {
}

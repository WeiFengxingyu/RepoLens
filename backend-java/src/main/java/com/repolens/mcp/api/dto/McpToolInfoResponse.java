package com.repolens.mcp.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

public record McpToolInfoResponse(
        String name,
        String description,
        @JsonProperty("input_schema")
        Map<String, Object> inputSchema,
        @JsonProperty("permission_policy")
        String permissionPolicy,
        boolean enabled
) {
}

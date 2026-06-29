package com.repolens.mcp.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record McpToolCallResponse(
        String id,
        @JsonProperty("tool_name")
        String toolName,
        String status,
        @JsonProperty("permission_decision")
        String permissionDecision,
        Object result,
        @JsonProperty("error_message")
        String errorMessage,
        McpToolCallAuditResponse audit
) {
}

package com.repolens.mcp.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.mcp.domain.McpToolCallAuditEntity;

import java.time.Instant;

public record McpToolCallAuditResponse(
        String id,
        @JsonProperty("task_id")
        String taskId,
        @JsonProperty("repository_id")
        String repositoryId,
        @JsonProperty("tool_name")
        String toolName,
        String status,
        @JsonProperty("permission_decision")
        String permissionDecision,
        @JsonProperty("permission_policy")
        String permissionPolicy,
        @JsonProperty("client_name")
        String clientName,
        @JsonProperty("client_session_id")
        String clientSessionId,
        @JsonProperty("input_hash")
        String inputHash,
        @JsonProperty("output_hash")
        String outputHash,
        @JsonProperty("input_summary")
        String inputSummary,
        @JsonProperty("output_summary")
        String outputSummary,
        @JsonProperty("latency_ms")
        Long latencyMs,
        @JsonProperty("error_message")
        String errorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("completed_at")
        Instant completedAt
) {
    public static McpToolCallAuditResponse from(McpToolCallAuditEntity entity) {
        return new McpToolCallAuditResponse(
                entity.getId(),
                entity.getTaskId(),
                entity.getRepositoryId(),
                entity.getToolName(),
                entity.getStatus(),
                entity.getPermissionDecision(),
                entity.getPermissionPolicy(),
                entity.getClientName(),
                entity.getClientSessionId(),
                entity.getInputHash(),
                entity.getOutputHash(),
                entity.getInputSummary(),
                entity.getOutputSummary(),
                entity.getLatencyMs(),
                entity.getErrorMessage(),
                entity.getCreatedAt(),
                entity.getCompletedAt()
        );
    }
}

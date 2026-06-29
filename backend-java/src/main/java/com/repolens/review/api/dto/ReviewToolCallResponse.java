package com.repolens.review.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.review.domain.ReviewToolCallEntity;

import java.time.Instant;

public record ReviewToolCallResponse(
        String id,
        @JsonProperty("tool_name")
        String toolName,
        String status,
        @JsonProperty("permission_decision")
        String permissionDecision,
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
    public static ReviewToolCallResponse from(ReviewToolCallEntity entity) {
        return new ReviewToolCallResponse(
                entity.getId(),
                entity.getToolName(),
                entity.getStatus(),
                entity.getPermissionDecision(),
                entity.getInputSummary(),
                entity.getOutputSummary(),
                entity.getLatencyMs(),
                entity.getErrorMessage(),
                entity.getCreatedAt(),
                entity.getCompletedAt()
        );
    }
}

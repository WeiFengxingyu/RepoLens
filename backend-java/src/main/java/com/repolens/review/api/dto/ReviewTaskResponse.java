package com.repolens.review.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.agent.api.dto.AgentTraceResponse;
import com.repolens.review.domain.ReviewTaskEntity;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record ReviewTaskResponse(
        @JsonProperty("task_id")
        String taskId,
        @JsonProperty("repository_id")
        String repositoryId,
        String status,
        String summary,
        @JsonProperty("risk_level")
        String riskLevel,
        List<Map<String, Object>> risks,
        @JsonProperty("impacted_symbols")
        List<String> impactedSymbols,
        @JsonProperty("suggested_tests")
        List<Map<String, Object>> suggestedTests,
        List<Map<String, Object>> citations,
        String markdown,
        @JsonProperty("tool_calls")
        List<ReviewToolCallResponse> toolCalls,
        List<AgentTraceResponse> traces,
        @JsonProperty("error_message")
        String errorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("completed_at")
        Instant completedAt
) {
    private static final TypeReference<List<Map<String, Object>>> MAP_LIST = new TypeReference<>() {
    };
    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };

    public static ReviewTaskResponse from(
            ReviewTaskEntity task,
            List<ReviewToolCallResponse> toolCalls,
            List<AgentTraceResponse> traces,
            ObjectMapper objectMapper
    ) {
        return new ReviewTaskResponse(
                task.getId(),
                task.getRepositoryId(),
                task.getStatus(),
                task.getSummary(),
                task.getRiskLevel(),
                read(objectMapper, task.getRisks(), MAP_LIST, List.of()),
                read(objectMapper, task.getImpactedSymbols(), STRING_LIST, List.of()),
                read(objectMapper, task.getSuggestedTests(), MAP_LIST, List.of()),
                read(objectMapper, task.getCitations(), MAP_LIST, List.of()),
                task.getMarkdown(),
                toolCalls,
                traces,
                task.getErrorMessage(),
                task.getCreatedAt(),
                task.getCompletedAt()
        );
    }

    private static <T> T read(ObjectMapper objectMapper, String value, TypeReference<T> type, T fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        try {
            return objectMapper.readValue(value, type);
        } catch (Exception ignored) {
            return fallback;
        }
    }
}

package com.repolens.agent.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.agent.domain.AgentTraceEntity;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record AgentTraceResponse(
        String id,
        @JsonProperty("step_name")
        String stepName,
        @JsonProperty("step_order")
        int stepOrder,
        String status,
        @JsonProperty("input_summary")
        String inputSummary,
        @JsonProperty("output_summary")
        String outputSummary,
        @JsonProperty("evidence_ids")
        List<String> evidenceIds,
        @JsonProperty("tool_calls")
        List<Map<String, Object>> toolCalls,
        @JsonProperty("token_usage")
        Map<String, Object> tokenUsage,
        @JsonProperty("latency_ms")
        Long latencyMs,
        @JsonProperty("error_message")
        String errorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("completed_at")
        Instant completedAt
) {
    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };
    private static final TypeReference<List<Map<String, Object>>> MAP_LIST = new TypeReference<>() {
    };
    private static final TypeReference<Map<String, Object>> MAP = new TypeReference<>() {
    };

    public static AgentTraceResponse from(AgentTraceEntity entity, ObjectMapper objectMapper) {
        return new AgentTraceResponse(
                entity.getId(),
                entity.getStepName(),
                entity.getStepOrder(),
                entity.getStatus(),
                entity.getInputSummary(),
                entity.getOutputSummary(),
                read(objectMapper, entity.getEvidenceIds(), STRING_LIST, List.of()),
                read(objectMapper, entity.getToolCalls(), MAP_LIST, List.of()),
                read(objectMapper, entity.getTokenUsage(), MAP, Map.of()),
                entity.getLatencyMs(),
                entity.getErrorMessage(),
                entity.getCreatedAt(),
                entity.getCompletedAt()
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

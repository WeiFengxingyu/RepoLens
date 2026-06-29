package com.repolens.evaluation.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.evaluation.domain.EvaluationRunEntity;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record EvaluationRunResponse(
        @JsonProperty("run_id")
        String runId,
        String name,
        @JsonProperty("dataset_path")
        String datasetPath,
        String strategy,
        String status,
        @JsonProperty("sample_count")
        int sampleCount,
        @JsonProperty("repository_map")
        Map<String, String> repositoryMap,
        List<EvaluationMetricResponse> metrics,
        List<EvaluationResultResponse> results,
        List<String> warnings,
        @JsonProperty("error_message")
        String errorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("started_at")
        Instant startedAt,
        @JsonProperty("completed_at")
        Instant completedAt
) {
    private static final TypeReference<Map<String, String>> STRING_MAP = new TypeReference<>() {
    };
    private static final TypeReference<List<EvaluationMetricResponse>> METRICS = new TypeReference<>() {
    };
    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };

    public static EvaluationRunResponse from(
            EvaluationRunEntity run,
            List<EvaluationResultResponse> results,
            ObjectMapper objectMapper
    ) {
        return new EvaluationRunResponse(
                run.getId(),
                run.getName(),
                run.getDatasetPath(),
                run.getStrategy(),
                run.getStatus(),
                run.getSampleCount(),
                read(objectMapper, run.getRepositoryMap(), STRING_MAP, Map.of()),
                read(objectMapper, run.getMetrics(), METRICS, List.of()),
                results,
                read(objectMapper, run.getWarnings(), STRING_LIST, List.of()),
                run.getErrorMessage(),
                run.getCreatedAt(),
                run.getStartedAt(),
                run.getCompletedAt()
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

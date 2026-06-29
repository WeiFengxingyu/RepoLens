package com.repolens.evaluation.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.evaluation.domain.EvaluationRunEntity;

import java.time.Instant;
import java.util.List;

public record EvaluationRunSummaryResponse(
        @JsonProperty("run_id")
        String runId,
        String name,
        @JsonProperty("dataset_path")
        String datasetPath,
        String strategy,
        String status,
        @JsonProperty("sample_count")
        int sampleCount,
        List<EvaluationMetricResponse> metrics,
        @JsonProperty("error_message")
        String errorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("completed_at")
        Instant completedAt
) {
    private static final TypeReference<List<EvaluationMetricResponse>> METRICS = new TypeReference<>() {
    };

    public static EvaluationRunSummaryResponse from(EvaluationRunEntity run, ObjectMapper objectMapper) {
        return new EvaluationRunSummaryResponse(
                run.getId(),
                run.getName(),
                run.getDatasetPath(),
                run.getStrategy(),
                run.getStatus(),
                run.getSampleCount(),
                read(objectMapper, run.getMetrics()),
                run.getErrorMessage(),
                run.getCreatedAt(),
                run.getCompletedAt()
        );
    }

    private static List<EvaluationMetricResponse> read(ObjectMapper objectMapper, String value) {
        if (value == null || value.isBlank()) {
            return List.of();
        }
        try {
            return objectMapper.readValue(value, METRICS);
        } catch (Exception ignored) {
            return List.of();
        }
    }
}

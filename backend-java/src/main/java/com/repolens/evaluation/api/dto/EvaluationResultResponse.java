package com.repolens.evaluation.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.evaluation.domain.EvaluationResultEntity;

import java.util.List;
import java.util.Map;

public record EvaluationResultResponse(
        String id,
        @JsonProperty("sample_id")
        String sampleId,
        @JsonProperty("sample_type")
        String sampleType,
        @JsonProperty("repository_key")
        String repositoryKey,
        String strategy,
        @JsonProperty("hit_at_5")
        boolean hitAt5,
        double mrr,
        @JsonProperty("citation_coverage")
        double citationCoverage,
        @JsonProperty("latency_ms")
        long latencyMs,
        @JsonProperty("token_count")
        int tokenCount,
        @JsonProperty("token_estimated")
        boolean tokenEstimated,
        @JsonProperty("matched_files")
        List<String> matchedFiles,
        @JsonProperty("matched_symbols")
        List<String> matchedSymbols,
        List<Map<String, Object>> citations,
        @JsonProperty("error_message")
        String errorMessage
) {
    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };
    private static final TypeReference<List<Map<String, Object>>> MAP_LIST = new TypeReference<>() {
    };

    public static EvaluationResultResponse from(EvaluationResultEntity entity, ObjectMapper objectMapper) {
        return new EvaluationResultResponse(
                entity.getId(),
                entity.getSampleId(),
                entity.getSampleType(),
                entity.getRepositoryKey(),
                entity.getStrategy(),
                entity.isHitAt5(),
                entity.getMrr(),
                entity.getCitationCoverage(),
                entity.getLatencyMs(),
                entity.getTokenCount(),
                entity.isTokenEstimated(),
                read(objectMapper, entity.getMatchedFiles(), STRING_LIST, List.of()),
                read(objectMapper, entity.getMatchedSymbols(), STRING_LIST, List.of()),
                read(objectMapper, entity.getCitations(), MAP_LIST, List.of()),
                entity.getErrorMessage()
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

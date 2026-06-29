package com.repolens.evaluation.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record EvaluationMetricResponse(
        String strategy,
        @JsonProperty("sample_count")
        int sampleCount,
        @JsonProperty("hit_at_5")
        double hitAt5,
        double mrr,
        @JsonProperty("citation_coverage")
        double citationCoverage,
        @JsonProperty("avg_latency_ms")
        double avgLatencyMs,
        @JsonProperty("p50_latency_ms")
        double p50LatencyMs,
        @JsonProperty("p95_latency_ms")
        double p95LatencyMs,
        @JsonProperty("avg_token_count")
        double avgTokenCount,
        @JsonProperty("token_estimated")
        boolean tokenEstimated,
        @JsonProperty("token_estimated_count")
        int tokenEstimatedCount,
        @JsonProperty("error_count")
        int errorCount
) {
}

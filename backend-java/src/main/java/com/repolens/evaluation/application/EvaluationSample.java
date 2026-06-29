package com.repolens.evaluation.application;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record EvaluationSample(
        String id,
        @JsonProperty("repository_key")
        String repositoryKey,
        @JsonProperty("sample_type")
        String sampleType,
        String query,
        @JsonProperty("expected_files")
        List<String> expectedFiles,
        @JsonProperty("expected_symbols")
        List<String> expectedSymbols
) {
    public EvaluationSample {
        expectedFiles = expectedFiles == null ? List.of() : List.copyOf(expectedFiles);
        expectedSymbols = expectedSymbols == null ? List.of() : List.copyOf(expectedSymbols);
    }
}

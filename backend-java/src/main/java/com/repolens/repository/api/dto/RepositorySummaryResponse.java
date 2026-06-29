package com.repolens.repository.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;

public record RepositorySummaryResponse(
        String id,
        String name,
        @JsonProperty("source_type")
        String sourceType,
        String status,
        @JsonProperty("file_count")
        int fileCount,
        @JsonProperty("chunk_count")
        int chunkCount,
        @JsonProperty("relation_count")
        int relationCount,
        @JsonProperty("updated_at")
        Instant updatedAt
) {
}

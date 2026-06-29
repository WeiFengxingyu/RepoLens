package com.repolens.repository.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.Map;

public record RepositoryDetailResponse(
        String id,
        String name,
        @JsonProperty("source_type")
        String sourceType,
        @JsonProperty("source_url")
        String sourceUrl,
        @JsonProperty("local_path")
        String localPath,
        String branch,
        @JsonProperty("commit_hash")
        String commitHash,
        String status,
        @JsonProperty("language_summary")
        Map<String, Integer> languageSummary,
        @JsonProperty("file_count")
        int fileCount,
        @JsonProperty("parsed_file_count")
        int parsedFileCount,
        @JsonProperty("skipped_file_count")
        int skippedFileCount,
        @JsonProperty("chunk_count")
        int chunkCount,
        @JsonProperty("relation_count")
        int relationCount,
        @JsonProperty("error_message")
        String errorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt,
        @JsonProperty("indexed_at")
        Instant indexedAt
) {
}

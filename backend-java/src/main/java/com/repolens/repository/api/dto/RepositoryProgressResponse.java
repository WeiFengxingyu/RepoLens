package com.repolens.repository.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RepositoryProgressResponse(
        @JsonProperty("current_step")
        String currentStep,
        @JsonProperty("file_count")
        int fileCount,
        @JsonProperty("parsed_file_count")
        int parsedFileCount,
        @JsonProperty("chunk_count")
        int chunkCount,
        @JsonProperty("relation_count")
        int relationCount
) {
}

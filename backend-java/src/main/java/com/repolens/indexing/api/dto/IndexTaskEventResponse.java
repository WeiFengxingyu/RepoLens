package com.repolens.indexing.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.indexing.domain.IndexTaskEventEntity;

import java.time.Instant;

public record IndexTaskEventResponse(
        String id,
        String stage,
        String status,
        String message,
        @JsonProperty("file_count")
        int fileCount,
        @JsonProperty("parsed_file_count")
        int parsedFileCount,
        @JsonProperty("chunk_count")
        int chunkCount,
        @JsonProperty("symbol_count")
        int symbolCount,
        @JsonProperty("relation_count")
        int relationCount,
        @JsonProperty("created_at")
        Instant createdAt
) {
    public static IndexTaskEventResponse from(IndexTaskEventEntity event) {
        return new IndexTaskEventResponse(
                event.getId(),
                event.getStage().name(),
                event.getStatus().name(),
                event.getMessage(),
                event.getFileCount(),
                event.getParsedFileCount(),
                event.getChunkCount(),
                event.getSymbolCount(),
                event.getRelationCount(),
                event.getCreatedAt()
        );
    }
}

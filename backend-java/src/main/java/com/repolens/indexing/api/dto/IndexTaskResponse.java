package com.repolens.indexing.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.indexing.domain.IndexTaskEntity;

import java.time.Instant;
import java.util.List;

public record IndexTaskResponse(
        String id,
        @JsonProperty("repository_id")
        String repositoryId,
        String status,
        @JsonProperty("current_stage")
        String currentStage,
        @JsonProperty("progress_percent")
        int progressPercent,
        @JsonProperty("last_error")
        String lastError,
        @JsonProperty("started_at")
        Instant startedAt,
        @JsonProperty("finished_at")
        Instant finishedAt,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt,
        List<IndexTaskEventResponse> events
) {
    public static IndexTaskResponse from(IndexTaskEntity task, List<IndexTaskEventResponse> events) {
        return new IndexTaskResponse(
                task.getId(),
                task.getRepositoryId(),
                task.getStatus().name(),
                task.getCurrentStage(),
                task.getProgressPercent(),
                task.getLastError(),
                task.getStartedAt(),
                task.getFinishedAt(),
                task.getCreatedAt(),
                task.getUpdatedAt(),
                events
        );
    }
}

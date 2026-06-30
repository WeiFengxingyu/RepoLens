package com.repolens.job.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.job.domain.AnalysisJobEntity;

import java.time.Instant;
import java.util.List;

public record JobResponse(
        String id,
        @JsonProperty("job_type")
        String jobType,
        String status,
        int priority,
        @JsonProperty("repository_id")
        String repositoryId,
        @JsonProperty("project_id")
        String projectId,
        @JsonProperty("idempotency_key")
        String idempotencyKey,
        @JsonProperty("payload_json")
        String payloadJson,
        @JsonProperty("result_ref")
        String resultRef,
        @JsonProperty("created_by")
        String createdBy,
        @JsonProperty("next_run_at")
        Instant nextRunAt,
        @JsonProperty("started_at")
        Instant startedAt,
        @JsonProperty("finished_at")
        Instant finishedAt,
        @JsonProperty("last_error_code")
        String lastErrorCode,
        @JsonProperty("last_error_message")
        String lastErrorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt,
        List<JobAttemptResponse> attempts,
        List<JobEventResponse> events
) {
    public static JobResponse from(AnalysisJobEntity entity, List<JobAttemptResponse> attempts, List<JobEventResponse> events) {
        return new JobResponse(
                entity.getId(),
                entity.getJobType().name(),
                entity.getStatus().name(),
                entity.getPriority(),
                entity.getRepositoryId(),
                entity.getProjectId(),
                entity.getIdempotencyKey(),
                entity.getPayloadJson(),
                entity.getResultRef(),
                entity.getCreatedBy(),
                entity.getNextRunAt(),
                entity.getStartedAt(),
                entity.getFinishedAt(),
                entity.getLastErrorCode(),
                entity.getLastErrorMessage(),
                entity.getCreatedAt(),
                entity.getUpdatedAt(),
                attempts,
                events
        );
    }
}

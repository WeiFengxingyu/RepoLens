package com.repolens.job.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.job.domain.JobAttemptEntity;

import java.time.Instant;

public record JobAttemptResponse(
        String id,
        @JsonProperty("job_id")
        String jobId,
        @JsonProperty("attempt_no")
        int attemptNo,
        @JsonProperty("worker_id")
        String workerId,
        String status,
        @JsonProperty("started_at")
        Instant startedAt,
        @JsonProperty("heartbeat_at")
        Instant heartbeatAt,
        @JsonProperty("finished_at")
        Instant finishedAt,
        @JsonProperty("error_code")
        String errorCode,
        @JsonProperty("error_message")
        String errorMessage
) {
    public static JobAttemptResponse from(JobAttemptEntity entity) {
        return new JobAttemptResponse(
                entity.getId(),
                entity.getJobId(),
                entity.getAttemptNo(),
                entity.getWorkerId(),
                entity.getStatus().name(),
                entity.getStartedAt(),
                entity.getHeartbeatAt(),
                entity.getFinishedAt(),
                entity.getErrorCode(),
                entity.getErrorMessage()
        );
    }
}

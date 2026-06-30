package com.repolens.job.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.job.domain.JobEventEntity;

import java.time.Instant;

public record JobEventResponse(
        String id,
        @JsonProperty("job_id")
        String jobId,
        @JsonProperty("attempt_id")
        String attemptId,
        @JsonProperty("event_type")
        String eventType,
        String message,
        @JsonProperty("payload_json")
        String payloadJson,
        @JsonProperty("created_at")
        Instant createdAt
) {
    public static JobEventResponse from(JobEventEntity entity) {
        return new JobEventResponse(
                entity.getId(),
                entity.getJobId(),
                entity.getAttemptId(),
                entity.getEventType(),
                entity.getMessage(),
                entity.getPayloadJson(),
                entity.getCreatedAt()
        );
    }
}

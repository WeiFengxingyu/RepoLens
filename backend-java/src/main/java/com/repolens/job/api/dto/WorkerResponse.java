package com.repolens.job.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.job.application.WorkerSnapshot;

import java.time.Instant;

public record WorkerResponse(
        @JsonProperty("worker_id")
        String workerId,
        String status,
        @JsonProperty("current_job_id")
        String currentJobId,
        @JsonProperty("heartbeat_at")
        Instant heartbeatAt
) {
    public static WorkerResponse from(WorkerSnapshot snapshot) {
        return new WorkerResponse(snapshot.workerId(), snapshot.status(), snapshot.currentJobId(), snapshot.heartbeatAt());
    }
}

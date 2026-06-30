package com.repolens.job.application;

import java.time.Instant;

public record WorkerSnapshot(
        String workerId,
        String status,
        String currentJobId,
        Instant heartbeatAt
) {
}

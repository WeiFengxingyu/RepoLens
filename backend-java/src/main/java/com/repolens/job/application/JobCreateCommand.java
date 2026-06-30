package com.repolens.job.application;

import com.repolens.job.domain.JobType;

public record JobCreateCommand(
        JobType jobType,
        String repositoryId,
        String projectId,
        String idempotencyKey,
        String payloadJson,
        String createdBy,
        Integer priority,
        boolean dispatch
) {
}

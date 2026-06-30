package com.repolens.job.domain;

public enum JobStatus {
    CREATED,
    QUEUED,
    RUNNING,
    SUCCEEDED,
    FAILED_RETRYABLE,
    RETRY_SCHEDULED,
    DEAD,
    CANCELED
}

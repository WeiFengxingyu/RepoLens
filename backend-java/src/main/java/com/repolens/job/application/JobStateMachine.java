package com.repolens.job.application;

import com.repolens.job.domain.JobStatus;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Set;

@Component
public class JobStateMachine {

    private static final Map<JobStatus, Set<JobStatus>> ALLOWED = Map.of(
            JobStatus.CREATED, Set.of(JobStatus.QUEUED, JobStatus.CANCELED),
            JobStatus.QUEUED, Set.of(JobStatus.RUNNING, JobStatus.CANCELED),
            JobStatus.RUNNING, Set.of(JobStatus.SUCCEEDED, JobStatus.FAILED_RETRYABLE, JobStatus.DEAD, JobStatus.CANCELED),
            JobStatus.FAILED_RETRYABLE, Set.of(JobStatus.RETRY_SCHEDULED, JobStatus.DEAD, JobStatus.CANCELED),
            JobStatus.RETRY_SCHEDULED, Set.of(JobStatus.QUEUED, JobStatus.CANCELED),
            JobStatus.SUCCEEDED, Set.of(),
            JobStatus.DEAD, Set.of(JobStatus.QUEUED),
            JobStatus.CANCELED, Set.of()
    );

    public void validate(JobStatus from, JobStatus to) {
        if (from == to) {
            return;
        }
        if (!ALLOWED.getOrDefault(from, Set.of()).contains(to)) {
            throw new IllegalStateException("Illegal job status transition: " + from + " -> " + to);
        }
    }
}
